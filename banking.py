import os
import random
import sqlite3
from enum import Enum


class Menu(Enum):
    EXIT = 0
    START = 1
    ACC_INFO = 2


class CustomerInfo:

    def __init__(self, card_num, pin, balance=0):
        self.card_num = card_num
        self.pin = pin
        self.balance = balance

    def check_pin(self, pin):
        return pin == self.pin

    def add_income(self, money, conn):
        self.balance += money
        self.update_balance(conn=conn)

    def transfer(self, transfer_customer, money, conn):
        if money > self.balance:
            print("Not enough money!\n")
            return
        self.balance -= money
        self.update_balance(conn)
        transfer_customer.add_income(money=money, conn=conn)
        print("""Success!\n""")

    def update_balance(self, conn):
        cur = conn.cursor()
        cur.execute(f"""UPDATE card
SET balance = {self.balance}
WHERE number = '{self.card_num}';""")
        conn.commit()

    def close_account(self, conn):
        cur = conn.cursor()
        cur.execute(f"""DELETE FROM card WHERE number = '{self.card_num}';""")
        conn.commit()


class BankingSystem:
    data_base = 'card.s3db'

    def __init__(self):
        self.customers = {}
        self.curr_customer = None
        self.curr_menu = Menu.START

        if os.path.isfile(path=self.data_base):
            self.conn = sqlite3.connect(self.data_base)
        else:
            self.create_db()

    def create_db(self):
        self.conn = sqlite3.connect(self.data_base)
        cur = self.conn.cursor()
        cur.execute("""    CREATE TABLE card ( 
       id integer primary key AUTOINCREMENT, 
       number TEXT, 
       pin TEXT, 
       balance INTEGER DEFAULT 0);""")
        self.conn.commit()

    def menu(self):

        while self.curr_menu != Menu.EXIT:
            if self.curr_menu == Menu.START:
                self.start_menu()
            elif self.curr_menu == Menu.ACC_INFO:
                self.account_menu()

        print("\nBye!")

    def account_menu(self):
        print("""1. Balance
2. Add income
3. Do transfer
4. Close account
5. Log out
0. Exit""")
        selected_menu = int(input())
        if selected_menu == 1:
            print(f"\nBalance: {self.curr_customer.balance}\n")
        elif selected_menu == 2:
            print("""\nEnter income:""")
            self.curr_customer.add_income(conn=self.conn, money=int(input()))
            print("Income was added!\n")
        elif selected_menu == 3:
            print("""\nTransfer
Enter card number:""")
            card = input()
            if card == self.curr_customer.card_num:
                print("You can't transfer money to the same account!\n")
                return
            transfer_customer = self.get_customer(customer_num=card)
            if transfer_customer is not None:
                print("""Enter how much money you want to transfer:""")
            else:
                if str(self.get_check_sum(number=card[0:-1])) == card[-1]:
                    print("""Such a card does not exist. \n""")
                else:
                    print("Probably you made mistake in card number. Please try again!\n")
                return
            money = int(input())
            self.curr_customer.transfer(transfer_customer=transfer_customer, money=money, conn=self.conn)
        elif selected_menu == 4:
            print("\nThe account has been closed!\n")
            self.curr_customer.close_account(conn=self.conn)
            self.curr_menu = Menu.START
        elif selected_menu == 5:
            print(f"\nYou have successfully logged out!\n")
            self.curr_menu = Menu.START
        elif selected_menu == 0:
            self.curr_menu = Menu.EXIT

    def start_menu(self):
        print("""1. Create an account
2. Log into account
0. Exit""")
        selected_menu = int(input())
        if selected_menu == 1:
            self.create_new_account()
        elif selected_menu == 2:
            self.login()
        elif selected_menu == 0:
            self.curr_menu = Menu.EXIT

    def check_exist_customers(self, card_num):
        cur = self.conn.cursor()
        cur.execute(f'SELECT COUNT(*) FROM card WHERE number = {card_num}')
        return cur.fetchone()

    def add_account_to_db(self, card_num, pin):
        cur = self.conn.cursor()
        cur.execute(f"INSERT INTO card (number, pin) VALUES ('{card_num}', {pin});")
        self.conn.commit()

    def create_new_account(self):
        pin = str(random.randint(0, 9999)).rjust(4, '0')
        bin = '400000'
        card_num = self.get_card_num(bin=bin)
        while card_num in self.check_exist_customers(card_num=card_num):
            card_num = self.get_card_num(bin=bin)
        self.add_account_to_db(card_num=card_num, pin=pin)
        print(f"""\nYour card has been created
Your card number:
{card_num}
Your card PIN:
{pin}""")

    def get_check_sum(self, number):
        myltipl_list = [int(digit) * 2 if num % 2 == 0 else int(digit) for num, digit in enumerate(number)]
        subst_over_9 = [digit - 9 if digit > 9 else digit for digit in myltipl_list]
        return (10 - (sum(subst_over_9) % 10)) % 10

    def get_card_num(self, bin):
        account_ident = str(random.randint(0, 999999999)).rjust(9, '0')
        check_sum = self.get_check_sum(number=f"{bin}{account_ident}")
        card_num = f"{bin}{account_ident}{check_sum}"
        return card_num

    def get_customer(self, customer_num):
        cur = self.conn.cursor()
        cur.execute(f'SELECT number, pin, balance FROM card WHERE number = {customer_num}')
        data = cur.fetchone()
        if data:
            [number, pin, balance] = data
            return CustomerInfo(card_num=number, pin=pin, balance=balance)
        return None

    def login(self):
        print("Enter your card number:")
        customer_num = input()

        self.curr_customer = self.get_customer(customer_num)

        print("Enter your PIN:")
        pin = input()
        if not (self.curr_customer is None) and self.curr_customer.check_pin(pin=pin):
            print("\nYou have successfully logged in!\n")
            self.curr_menu = Menu.ACC_INFO
        else:
            print("\nWrong card number or PIN!\n")


if __name__ == "__main__":
    test = BankingSystem()
    test.menu()
