from datetime import datetime
from dateutil.relativedelta import relativedelta
from database.db_manager import DBManager
from models.category import Category
from models.transaction import Transaction
from models.commitment import Commitment, CommitmentPayment
from models.savings import SavingsGoal, SavingsContribution

class FinanceController:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    @staticmethod
    def _normalize_recurrence(r_type, r_interval=1, r_duration=None):
        if r_type in (None, "", "one_time"):
            return "one_time", 1, None

        interval = max(1, int(r_interval or 1))
        duration = None if r_duration in (None, "", 0) else max(1, int(r_duration))
        return "custom", interval, duration

    @staticmethod
    def _is_recurring_type(r_type):
        return r_type not in (None, "", "one_time")

    def get_categories(self, t_type=None):
        rows = self.db.get_categories(t_type)
        return [Category.from_db_row(row) for row in rows]

    def get_category_by_id(self, cat_id):
        row = self.db.get_category_by_id(cat_id)
        if row:
            return Category.from_db_row(row)
        return None

    def add_category(self, name, c_type, color):
        return self.db.add_category(name, c_type, color)

    def delete_category(self, cat_id):
        self.db.delete_category(cat_id)

    def update_category(self, cat_id, name, c_type, color):
        self.db.update_category(cat_id, name, c_type, color)

    def get_transactions(self, t_type=None):
        rows = self.db.get_transactions(t_type)
        return [Transaction.from_db_row(row) for row in rows]

    def get_transaction_by_id(self, t_id):
        row = self.db.get_transaction_by_id(t_id)
        if row:
            return Transaction.from_db_row(row)
        return None

    def add_transaction(self, t_type, category_id, name, amount, date, r_type='one_time', r_interval=1, r_duration=None):
        r_type, r_interval, r_duration = self._normalize_recurrence(r_type, r_interval, r_duration)
        return self.db.add_transaction(t_type, category_id, name, amount, date, r_type, r_interval, r_duration)
        
    def update_transaction(self, t_id, category_id, name, amount, date, r_type='one_time', r_interval=1, r_duration=None):
        # Get the original transaction to see if it's recurring and has history
        old_tx = self.get_transaction_by_id(t_id)
        new_type, new_interval, new_duration = self._normalize_recurrence(r_type, r_interval, r_duration)
        
        if old_tx and self._is_recurring_type(old_tx.recurrence_type):
            try:
                start_date_old = datetime.strptime(old_tx.date, "%Y-%m-%d")
                start_date_new = datetime.strptime(date, "%Y-%m-%d")
                old_type, old_interval, _ = self._normalize_recurrence(
                    old_tx.recurrence_type, old_tx.recurrence_interval, old_tx.recurrence_duration
                )
                
                # Calculate months difference
                months_diff = (start_date_new.year - start_date_old.year) * 12 + (start_date_new.month - start_date_old.month)
                
                # Number of occurrences already passed
                num_occurrences_past = months_diff // old_interval
                
                # If it's a future edit (meaning some occurrences have already passed since the original start)
                if num_occurrences_past > 0:
                    # 1. Update old transaction to end BEFORE the new date
                    # We set the duration to how many times it has run so far
                    self.db.update_transaction(
                        t_id, old_tx.category_id, old_tx.name, old_tx.amount, old_tx.date, 
                        old_type, old_interval, num_occurrences_past
                    )
                    
                    # 2. Create a NEW transaction from the new date onwards
                    # Note: If the user provided a custom duration, we should subtract the past ones
                    if new_duration is not None and old_tx.recurrence_duration is not None:
                         # This part is tricky, but let's assume r_duration passed from UI is the TOTAL new duration 
                         # or if the user didn't change it, it's the remaining. 
                         # Usually r_duration=None means indefinite.
                         pass

                    return self.db.add_transaction(old_tx.type, category_id, name, amount, date, new_type, new_interval, new_duration)
            except Exception as e:
                print(f"Error in future-edit logic: {e}")

        # Default standard update
        self.db.update_transaction(t_id, category_id, name, amount, date, new_type, new_interval, new_duration)

    def delete_transaction(self, t_id):
        # Before deleting, check if this expense has a matching commitment payment
        tx = self.get_transaction_by_id(t_id)
        if tx and tx.type == 'expense':
            self._remove_matching_commitment_payment(tx.amount, tx.date)
        self.db.delete_transaction(t_id)

    def _remove_matching_commitment_payment(self, amount, date):
        """
        Find and remove a single commitment payment that matches the given
        amount and date. This reverses the money deducted from the commitment.
        Uses a tolerance of 0.01 for float comparison.
        """
        all_payments = self.db.get_all_commitment_payments_decrypted()
        for pay in all_payments:
            # pay tuple: (id, commitment_id, amount, date)
            pay_id, _, pay_amount, pay_date = pay
            if pay_date == date and abs(pay_amount - amount) < 0.01:
                self.db.delete_commitment_payment(pay_id)
                return  # Only remove ONE matching payment

    def get_transactions_for_month(self, year, month):
        """
        Returns a tuple of (incomes, expenses) lists active in the specified year and month,
        resolving recurrences.
        """
        all_tx = self.get_transactions()
        active_incomes = []
        active_expenses = []

        target_date = datetime(year, month, 1)

        for tx in all_tx:
            start_date = datetime.strptime(tx.date, "%Y-%m-%d")
            # Calculate months diff
            months_diff = (target_date.year - start_date.year) * 12 + (target_date.month - start_date.month)

            is_active = False

            if not self._is_recurring_type(tx.recurrence_type):
                if months_diff == 0:
                    is_active = True
            else:
                interval = max(1, tx.recurrence_interval or 1)
                if months_diff >= 0 and months_diff % interval == 0:
                    occurrence_num = (months_diff // interval) + 1
                    if tx.recurrence_duration is None or occurrence_num <= tx.recurrence_duration:
                        is_active = True

            if is_active:
                if tx.type == 'income':
                    active_incomes.append(tx)
                else:
                    active_expenses.append(tx)

        return active_incomes, active_expenses

    def get_dashboard_summary(self, year, month):
        incomes, expenses = self.get_transactions_for_month(year, month)
        
        total_income = sum(i.amount for i in incomes)
        total_expense = sum(e.amount for e in expenses)
        balance = total_income - total_expense

        # Expenses by item, sorted by category to cluster slices of the same color
        expenses_breakdown = []
        for e in sorted(expenses, key=lambda x: x.category_id):
            cat = self.get_category_by_id(e.category_id)
            if cat:
                expenses_breakdown.append({
                    'name': e.name,
                    'amount': e.amount,
                    'color': cat.color,
                    'category_name': cat.name
                })

        return {
            'total_income': total_income,
            'total_expense': total_expense,
            'balance': balance,
            'expenses_breakdown': expenses_breakdown
        }

    def get_trend_data(self, end_year, end_month, num_months=6):
        """
        Returns incomes and expenses totals for the last `num_months` months ending in target date.
        """
        trend_incomes = []
        trend_expenses = []
        labels = []

        end_date = datetime(end_year, end_month, 1)
        start_date = end_date - relativedelta(months=num_months-1)

        current_date = start_date
        while current_date <= end_date:
            inc, exp = self.get_transactions_for_month(current_date.year, current_date.month)
            trend_incomes.append(sum(i.amount for i in inc))
            trend_expenses.append(sum(e.amount for e in exp))
            labels.append(current_date.strftime("%b %y"))
            current_date += relativedelta(months=1)

        return {
            'labels': labels,
            'incomes': trend_incomes,
            'expenses': trend_expenses
        }

    def get_full_history_data(self):
        """
        Returns all historical data grouped by month from the first transaction to current month.
        """
        all_tx = self.get_transactions()
        if not all_tx:
            return {'labels': [], 'incomes': [], 'expenses': [], 'balances': []}
            
        # Find earliest date
        try:
            earliest_date = datetime.strptime(all_tx[0].date, "%Y-%m-%d")
        except:
            earliest_date = datetime.now()
            
        for tx in all_tx:
            try:
                d = datetime.strptime(tx.date, "%Y-%m-%d")
                if d < earliest_date:
                    earliest_date = d
            except:
                pass
                
        now = datetime.now()
        start_date = datetime(earliest_date.year, earliest_date.month, 1)
        end_date = datetime(now.year, now.month, 1)
        
        hist_incomes = []
        hist_expenses = []
        hist_balances = []
        labels = []
        
        current_date = start_date
        while current_date <= end_date:
            inc, exp = self.get_transactions_for_month(current_date.year, current_date.month)
            inc_sum = sum(i.amount for i in inc)
            exp_sum = sum(e.amount for e in exp)
            
            hist_incomes.append(inc_sum)
            hist_expenses.append(exp_sum)
            hist_balances.append(inc_sum - exp_sum)
            labels.append(current_date.strftime("%b %y"))
            
            current_date += relativedelta(months=1)
            
        return {
            'labels': labels,
            'incomes': hist_incomes,
            'expenses': hist_expenses,
            'balances': hist_balances
        }

    # --- COMMITMENTS ---
    def add_commitment(self, name, total_amount, date):
        return self.db.add_commitment(name, total_amount, date)

    def delete_commitment(self, c_id):
        self.db.delete_commitment(c_id)

    def update_commitment(self, c_id, name, total_amount, date):
        self.db.update_commitment(c_id, name, total_amount, date)

    def add_commitment_payment(self, commitment_id, amount, date):
        return self.db.add_commitment_payment(commitment_id, amount, date)

    def get_commitments_with_progress(self):
        rows = self.db.get_commitments()
        commitments = []
        for r in rows:
            c = Commitment.from_db_row(r)
            pay_rows = self.db.get_commitment_payments(c.id)
            total_paid = sum([pay[2] for pay in pay_rows])
            remaining = c.total_amount - total_paid
            commitments.append({
                'commitment': c,
                'total_paid': total_paid,
                'remaining': remaining,
                'progress_pct': (total_paid / c.total_amount * 100) if c.total_amount > 0 else 100,
                'payments': pay_rows  # raw decrypted tuples: (id, c_id, amount, date)
            })
        return commitments
        
    def get_active_commitments(self):
        """Returns commitments that still have a remaining balance > 0."""
        return [c for c in self.get_commitments_with_progress() if c['remaining'] > 0]

    def get_commitments_summary(self):
        comms = self.get_commitments_with_progress()
        total_pending = sum(c['remaining'] for c in comms)
        
        # Calculate average monthly income to estimate months to pay
        hist = self.get_full_history_data()
        incomes = hist['incomes']
        
        # Filter 0s to get a true average of months with income
        valid_incomes = [i for i in incomes if i > 0]
        avg_monthly_income = sum(valid_incomes) / len(valid_incomes) if valid_incomes else 0
        
        months_to_pay = (total_pending / avg_monthly_income) if avg_monthly_income > 0 else float('inf')
        
        return {
            'total_pending': total_pending,
            'avg_monthly_income': avg_monthly_income,
            'months_to_pay_estimation': months_to_pay
        }

    # --- FINANCIAL HEALTH ---
    def get_financial_health_metrics(self):
        # We can analyze the last 6 months or full history. Let's do full year or last 6 months for a realistic current state
        now = datetime.now()
        trend = self.get_trend_data(now.year, now.month, 6)
        
        total_inc = sum(trend['incomes'])
        total_exp = sum(trend['expenses'])
        
        savings_rate = 0
        if total_inc > 0:
            savings_rate = ((total_inc - total_exp) / total_inc) * 100
            
        # 50/30/20 Rule Analysis (Needs to get categories)
        # 50% Needs (Vivienda, Comida, Transporte)
        # 30% Wants (Ocio, Suscripciones)
        # 20% Savings
        # We'll approximate this by categorizing expenses
        
        # Let's pull expenses for the last 6 months specifically to categorize them
        total_needs = 0
        total_wants = 0
        
        # Just loop over last 6 months
        end_date = datetime(now.year, now.month, 1)
        start_date = end_date - relativedelta(months=5)
        
        current_date = start_date
        while current_date <= end_date:
            _, exp = self.get_transactions_for_month(current_date.year, current_date.month)
            for e in exp:
                cat = self.get_category_by_id(e.category_id)
                if cat:
                    name_lower = cat.name.lower()
                    if any(n in name_lower for n in ['vivienda', 'comida', 'transporte', 'salud', 'hipoteca']):
                        total_needs += e.amount
                    else:
                        total_wants += e.amount
            current_date += relativedelta(months=1)
            
        rule_needs_pct = (total_needs / total_inc * 100) if total_inc > 0 else 0
        rule_wants_pct = (total_wants / total_inc * 100) if total_inc > 0 else 0
        rule_savings_pct = savings_rate
        
        # Score calculation (0-100)
        # Base 50, +20 if savings > 20%, +15 if needs < 50%, +15 if wants < 30%
        score = 50
        if rule_savings_pct >= 20: score += 20
        elif rule_savings_pct > 0: score += 10
        if rule_needs_pct <= 50 and rule_needs_pct > 0: score += 15
        if rule_wants_pct <= 30 and rule_wants_pct > 0: score += 15
        
        return {
            'avg_monthly_income': total_inc / 6,
            'avg_monthly_expense': total_exp / 6,
            'savings_rate': rule_savings_pct,
            'needs_pct': rule_needs_pct,
            'wants_pct': rule_wants_pct,
            'score': score
        }

    # --- SAVINGS / HUCHAS ---
    def add_savings_goal(self, name, target_amount, date):
        return self.db.add_savings_goal(name, target_amount, date)

    def delete_savings_goal(self, s_id):
        self.db.delete_savings_goal(s_id)

    def add_savings_contribution(self, savings_id, amount, date):
        return self.db.add_savings_contribution(savings_id, amount, date)

    def get_savings_goals_with_progress(self):
        rows = self.db.get_savings_goals()
        goals = []
        for r in rows:
            g = SavingsGoal.from_db_row(r)
            cont_rows = self.db.get_savings_contributions(g.id)
            total_saved = sum([c[2] for c in cont_rows])
            
            progress_pct = 0
            if g.target_amount > 0:
                progress_pct = (total_saved / g.target_amount * 100)
            elif g.target_amount == 0:
                progress_pct = 100 # Or maybe handle display differently in UI
                
            goals.append({
                'goal': g,
                'total_saved': total_saved,
                'progress_pct': progress_pct,
                'contributions': cont_rows
            })
        return goals
