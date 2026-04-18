import os
import json
import urllib.request
import urllib.error

class SyncManager:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def _get_config(self):
        enabled = self.db.get_config('sync_enabled') == '1'
        url = self.db.get_config('sync_url')
        token = self.db.get_config('sync_token')
        return enabled, url, token
        
    def sync_bidirectional(self):
        """Sincronización principal."""
        enabled, url, token = self._get_config()
        if not enabled or not url or not token:
            return False, "Sincronización no configurada o apagada."
            
        try:
            # 1. Comprobar status del servidor
            req = urllib.request.Request(f"{url}/api/sync/status", headers={'Authorization': f'Bearer {token}'})
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status != 200:
                        return False, f"Error del servidor: {response.status}"
                    data = json.loads(response.read().decode())
                    remote_updated = int(data.get('last_updated', 0))
            except urllib.error.URLError as e:
                return False, f"Servidor no alcanzable: {str(e)}"
                
            local_updated_str = self.db.get_config('last_updated')
            local_updated = int(local_updated_str) if local_updated_str else 0
            
            # Margen de 2 segundos para evitar loops
            if abs(remote_updated - local_updated) < 2000:
                return True, "Sincronizado (No hay cambios)"
                
            if remote_updated > local_updated:
                # El servidor es más nuevo -> PULL
                req_dl = urllib.request.Request(f"{url}/api/sync/download", headers={'Authorization': f'Bearer {token}'})
                with urllib.request.urlopen(req_dl, timeout=15) as response:
                    tmp_path = self.db.db_path + '.tmp'
                    with open(tmp_path, 'wb') as f:
                        f.write(response.read())
                
                os.replace(tmp_path, self.db.db_path)
                return True, "Datos descargados del servidor."
            else:
                # El local es más nuevo -> PUSH
                with open(self.db.db_path, 'rb') as f:
                    db_data = f.read()
                req_up = urllib.request.Request(
                    f"{url}/api/sync/upload", 
                    data=db_data, 
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/octet-stream'}
                )
                with urllib.request.urlopen(req_up, timeout=15) as response:
                    if response.status == 200:
                        return True, "Datos subidos al servidor."
                        
            return False, "Estado indetectado."
        except Exception as e:
            return False, f"Fallo al sincronizar: {str(e)}"
