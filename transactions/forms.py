from django import forms
from .models import Transaction
from accounts.models import UserBankAccount
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account') # account value ke pop kore anlam
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput() # user er theke hide kora thakbe

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):
    def clean_amount(self): # amount field ke filter korbo
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') # user er fill up kora form theke amra amount field er value ke niye aslam, 50
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance # 1000
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance: # amount = 5000, tar balance ache 200
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount



class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount
    
class TransferMoneyForm(forms.ModelForm):
    receiver_account = forms.ModelChoiceField(queryset=UserBankAccount.objects.all(), label="Transfer To")

    class Meta:
        model = Transaction
        fields = ['receiver_account', 'amount']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
        # Exclude the user's own account from the queryset
        if self.account:
            self.fields['receiver_account'].queryset = UserBankAccount.objects.exclude(id=self.account.id)

    def clean(self):
        cleaned_data = super().clean()
        from_account = self.account
        receiver_account = cleaned_data.get("receiver_account")
        amount = cleaned_data.get("amount")

        if from_account == receiver_account:
            raise forms.ValidationError("You cannot transfer money to the same account.")

        if amount <= 0:
            raise forms.ValidationError("The transfer amount must be greater than zero.")

        if from_account.balance < amount:
            raise forms.ValidationError("Insufficient funds in the source account.")

        return cleaned_data