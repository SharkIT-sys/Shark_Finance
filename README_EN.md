<h1 align="center">
  <img src="ui/resources/logo.png" alt="Shark Logo" width="120">
  <br>
  Shark Accounting
</h1>

<p align="center">
  <strong>The hyper-secure and versatile Desktop financial manager with Cloud PWA deployment.</strong>
</p>

---

**Shark Accounting** is a budget manager designed to give users the rigor of professional business in their daily home finances, shielded with a level of security and cryptography that ensures data remains readable only in the environment of the legitimate owner.

## ✨ Main Features

* **Real AES-256 Encryption**: Database fields (Income, Expenses, and Commitments) are not saved in plain text. They are raw encrypted.
* **Secure Protocol System**: Complete self-destruction of the local database and its master directory against hacks (5 failed authentication attempts).
* **Commitments and Payment Plans**: You don't just record past expenses. The "Commitments" system takes ownership of your long-term debts or purchases, calculating your paid percentage and the mathematically estimated time remaining to finish your debt.
* **Piggy Banks and Savings Goals**: The reverse of commitments. Create piggy banks with a target (e.g., Travel) or without a ceiling (e.g., Emergency Fund). Each contribution counts as an expense for your pocket but a success for your goal.
* **Universal 50/30/20 Rule**: The app diagnoses your economic health by assigning an automated monthly score from 0-100 to evaluate if you achieve the mythical balance of Needs / Wants / Savings.
* **Extreme Portability and Flexibility**: Database export to external storage (USB) capable of restarting on another machine and requesting the original key to reveal balances.

## 📱 Integrated Server and PWA Web

Your desktop client is not limited to the PC. It has an internal **Server Center** hub that with one click:
1. Deploys a background `Flask` server to enter expenses from your mobile on the same WiFi network.
2. Generates a code `.zip` exporter.
3. Offers a Remote Installer (Zero-Touch) to inject a self-managed Shark Docker Container into third-party VPS infrastructures via `SSH`.

Once your external server is deployed (Docker), you will enjoy **Integrated Cloud Save**:
- **Automatic Sync (Bidirectional)**: Every time you open the app on your PC, the latest movements you entered on your mobile/web will be downloaded. Everything you change on the Desktop will be uploaded to the Server upon closing.

## 🛠 Installation and Configuration

The project is designed to be deployed using `PyInstaller` as a single `.exe` on Windows clients, or run under source code without hidden dependencies.

**Requirements**: Python 3.10+ and PyQt6.

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-web.txt

# Start the Local Native App
python main.py

# Auto-Package App for distribution (Windows)
pyinstaller "Shark Contabilidad.spec" --clean -y
```

## ⚖️ License
This project is governed under the strict margins of the **Creative Commons Attribution-NonCommercial 4.0** license (CC BY-NC 4.0).
- Requires attribution of the code.
- Explicitly limits or legally penalizes **any** commercial purpose or monetized distribution of its logical layer without the direct signed consent of its Creator. (See `/LICENSE_EN`).
