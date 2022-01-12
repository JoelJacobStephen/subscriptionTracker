import datetime
import math
import tkinter as tk
import tkinter.messagebox as mb
import tkinter.ttk as ttk
import calendar
import mysql.connector
from tkcalendar import DateEntry

# Connecting to the Database
subscription_db = mysql.connector.connect(
    host="localhost", user="root", passwd="joel1007", database="subscription")
print(subscription_db)

if subscription_db:
    print("Database Connected")
else:
    print("Database Connection Failed")

connector = subscription_db.cursor()

connector.execute(
    'CREATE TABLE IF NOT EXISTS SubscriptionTracker (ID INT PRIMARY KEY NOT NULL AUTO_INCREMENT, Date DATE, '
    'BillDate DATE, '
    'Category VARCHAR(20), Description VARCHAR(20), Amount INT, ModeOfPayment VARCHAR(20), Cycle VARCHAR(20)); '
)

for db in connector:
    print(db)


# Functions

# Add years to the given date
def add_years(d, years):
    try:
        # Return same day of the current year
        return d.replace(year=d.year + years)
    except ValueError:
        # If not same day, it will return other, i.e.  February 29 to March 1 etc.
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))


# Add months to the given date
def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


# Lists all the subscriptions
def list_all_subscriptions():
    global connector, table

    table.delete(*table.get_children())
    display = 'SELECT * FROM subscriptiontracker'

    connector.execute(display)
    data = connector.fetchall()

    for values in data:
        table.insert('', tk.END, values=values)

    # display = 'SELECT * FROM subscriptiontracker'

    # values = 'SELECT * FROM subscriptiontracker'
    # connector.execute(display)
    # data = connector.fetchall()
    #
    # processed_data = []
    #
    # for index, values in enumerate(data):
    #     value_list = list(values)
    #     value_list[0] = index + 1
    #     processed_data.append(tuple(value_list))


# Clear all input fields
def clear_fields():
    global desc, category, amount, MoP, date, table

    today_date = datetime.datetime.now().date()

    desc.set('')
    category.set('')
    amount.set(0.0)
    MoP.set('Cash'), date.set_date(today_date)
    table.selection_remove(*table.selection())


# View Subscription Details
def view_subscription_details():
    global table
    global date, category, desc, amount, MoP

    if not table.selection():
        mb.showerror('No subscriptions selected',
                     'Please select an subscription from the table to view its details')

    current_selected_subscription = table.item(table.focus())
    values = current_selected_subscription['values']

    expenditure_date = datetime.date(
        int(values[1][:4]), int(values[1][5:7]), int(values[1][8:]))

    date.set_date(expenditure_date)
    category.set(values[3])
    desc.set(values[4])
    amount.set(values[5])
    MoP.set(values[6])


# Delete Subscriptions
def remove_subscriptions():
    if not table.selection():
        mb.showerror('No record selected!',
                     'Please select a record to delete!')
        return

    current_selected_subscription = table.item(table.focus())
    values_selected = current_selected_subscription['values']

    surety = mb.askyesno(
        'Are you sure?', f'Are you sure that you want to delete the record of {values_selected[4]}')

    if surety:
        connector.execute(
            'SELECT ID FROM SubscriptionTracker WHERE ID=%d' % values_selected[0])
        id_num = connector.fetchall()
        id_number = id_num[0][0]
        print(id_number)

        connector.execute(
            'DELETE FROM SubscriptionTracker WHERE ID=%d' % values_selected[0])
        subscription_db.commit()

        connector.execute(f'ALTER TABLE subscriptiontracker AUTO_INCREMENT = {id_number - 1};')
        subscription_db.commit()

        list_all_subscriptions()
        mb.showinfo('Record deleted successfully!',
                    'The record you wanted to delete has been deleted successfully')


# Delete all subscriptions
def remove_all_subscriptions():
    surety = mb.askyesno(
        'Are you sure?', 'Are you sure that you want to delete all the subscription items from the database?',
        icon='warning')

    if surety:
        table.delete(*table.get_children())

        connector.execute('DELETE FROM SubscriptionTracker')
        subscription_db.commit()

        clear_fields()
        list_all_subscriptions()
        mb.showinfo('All Subscriptions deleted',
                    'All the subscriptions were successfully deleted')
    else:
        mb.showinfo(
            'Ok then', 'The task was aborted and no subscription was deleted!')


# Add a subscription
def add_subscriptions():
    global date, category, desc, amount, MoP, cycle
    global connector

    bill_date = date.get_date()

    if cycle.get() == 'Yearly':
        bill_date = add_years(date.get_date(), 1)
    elif cycle.get() == 'Monthly':
        bill_date = add_months(date.get_date(), 1)
    elif cycle.get() == 'Half Yearly':
        bill_date = add_months(date.get_date(), 6)

    if not date.get() or not category.get() or not desc.get() or not amount.get() or not MoP.get():
        mb.showerror(
            'Fields empty!', "Please fill all the missing fields!")
    else:
        record = (date.get_date(), bill_date, category.get(),
                  desc.get(), amount.get(), MoP.get(), cycle.get())

        insertion = 'INSERT INTO SubscriptionTracker (Date, BillDate, Category, Description, Amount, ModeOfPayment, ' \
                    'Cycle) ' \
                    'VALUES (%s, ' \
                    '%s, %s, %s, %s, %s, %s); '

        connector.execute(insertion, record)
        subscription_db.commit()

        list_all_subscriptions()
        clear_fields()
        subscription_db.commit()

        clear_fields()
        list_all_subscriptions()
        mb.showinfo(
            'Subscription added', 'The Subscription details has been added to the database')


# Edit a subscription
def edit_subscription():
    global table

    def edit_existing_subscriptions():
        global date, amount, desc, category, MoP
        global connector, table

        current_selected_subscription = table.item(table.focus())
        contents = current_selected_subscription['values']

        record = (date.get_date(), category.get(),
                  desc.get(), amount.get(), MoP.get(), contents[0])

        connector.execute(
            'UPDATE SubscriptionTracker SET Date = %s, Category = %s, Description = %s, Amount = %s, ModeOfPayment = '
            '%s '
            'WHERE ID = %s',
            record)
        subscription_db.commit()

        clear_fields()
        list_all_subscriptions()

        mb.showinfo(
            'Data edited', 'Data updated and stored in the database')
        edit_btn.destroy()
        return

    if not table.selection():
        mb.showerror('No subscription selected!',
                     'You have not selected any subscription to edit!')
        return

    view_subscription_details()

    edit_btn = tk.Button(data_entry_frame, text='Edit Subscription', font=btn_font, width=30,
                         bg=button_bg, command=edit_existing_subscriptions)
    edit_btn.place(x=10, y=395)


# Shows us those subscriptions that have to be paid in less than 7 days
def remainder():
    frame = tk.Frame(root, bd=3, bg='#00bcd4')
    frame.place(relx=0.1, rely=0.12, relheight=0.08, relwidth=0.8)

    global sub_menu
    sub_menu = tk.Label(frame, bd=5, font=('Helvetica', 15, 'bold'),
                        anchor='nw', justify='center', fg='#00948f', text="Remainders")
    sub_menu.place(relx=0.43, rely=0.11, relheight=0.79, relwidth=0.13)

    global label
    label = tk.Label(bottom_frame, bd=2, bg='#fffcfc', font=(
        'Helvetica', 15, 'bold'), anchor='nw', justify='left', fg='#00bcd4')
    label.place(relx=0.05, rely=0.05, relheight=0.9, relwidth=0.9)

    menu_button = tk.Button(bottom_frame, bd=3, text="Menu", font=(
        'Helvetica', 13, 'bold'), bg='#00bcd4', fg='#fffcfc', command=menu)
    menu_button.place(relx=0.75, rely=0.05, relwidth=0.2, relheight=0.1)

    # Database Connection
    connector.execute('SELECT BillDate FROM subscriptiontracker; ')
    data = connector.fetchall()

    connector.execute('SELECT Count(*) FROM subscriptiontracker; ')
    countlist = connector.fetchall()
    count = countlist[0][0]

    d1 = datetime.datetime.now().date()

    for i in range(count):
        d2 = data[i][0]
        remaining = d2 - d1
        if remaining.days <= 5:
            connector.execute(f"SELECT Count(*) FROM subscriptiontracker WHERE BillDate = '{d2}'; ")
            count_sub = connector.fetchall()
            sub_count = count_sub[0][0]

            connector.execute(f"SELECT Description FROM subscriptiontracker WHERE BillDate = '{d2}'; ")
            pending_sub = connector.fetchall()
            break

    for i in range(sub_count):
        label['text'] += f" {i + 1}. {pending_sub[i][0]} => {remaining.days} days left to pay \n"


# Gives a detailed report on subscriptions in the database
def subscription_reports():
    frame = tk.Frame(root, bd=3, bg='#00bcd4')
    frame.place(relx=0.1, rely=0.12, relheight=0.08, relwidth=0.8)

    global sub_menu
    sub_menu = tk.Label(frame, bd=5, font=('Helvetica', 15, 'bold'),
                        anchor='nw', justify='center', fg='#00948f', text="Subscriptions Report")
    sub_menu.place(relx=0.43, rely=0.11, relheight=0.79, relwidth=0.22)

    global label
    label = tk.Label(bottom_frame, bd=2, bg='#fffcfc', font=(
        'Helvetica', 15, 'bold'), anchor='nw', justify='left', fg='#00bcd4')
    label.place(relx=0.05, rely=0.05, relheight=0.9, relwidth=0.9)

    count = 'SELECT COUNT(Description) FROM subscriptiontracker'

    yearly_amount = 0
    monthly_amount = 0
    half_yearly_amount = 0

    connector.execute(count)
    total_sub = connector.fetchall()

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly"')
    amount = connector.fetchall()
    yearly_amount = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly"')
    amount = connector.fetchall()
    monthly_amount = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly"')
    amount = connector.fetchall()
    half_yearly_amount = amount[0][0]

    if yearly_amount is None:
        yearly_amount = 0

    if monthly_amount is None:
        monthly_amount = 0

    if half_yearly_amount is None:
        half_yearly_amount = 0

    total_amount = yearly_amount + (monthly_amount * 12) + (half_yearly_amount * 2)

    # Music
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Music"')
    amount = connector.fetchall()
    music_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Music"')
    amount = connector.fetchall()
    music_monthly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Music"')
    amount = connector.fetchall()
    music_half_yearly = amount[0][0]

    if music_yearly is None:
        music_yearly = 0

    if music_monthly is None:
        music_monthly = 0

    if music_half_yearly is None:
        music_half_yearly = 0

    total_music = music_yearly + (music_monthly * 12) + (music_half_yearly * 2)

    # Gaming
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Gaming"')
    amount = connector.fetchall()
    gaming_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Gaming"')
    amount = connector.fetchall()
    gaming_monthly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Gaming"')
    amount = connector.fetchall()
    gaming_half_yearly = amount[0][0]

    if gaming_yearly is None:
        gaming_yearly = 0

    if gaming_monthly is None:
        gaming_monthly = 0

    if gaming_half_yearly is None:
        gaming_half_yearly = 0

    total_gaming = gaming_yearly + (gaming_monthly * 12) + (gaming_half_yearly * 2)

    # Phone
    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Phone/Internet"')
    amount = connector.fetchall()
    phone_yearly = amount[0][0]

    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Phone/Internet"')
    amount = connector.fetchall()
    phone_monthly = amount[0][0]

    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Phone/Internet"')
    amount = connector.fetchall()
    phone_half_yearly = amount[0][0]

    if phone_yearly is None:
        phone_yearly = 0

    if phone_monthly is None:
        phone_monthly = 0

    if phone_half_yearly is None:
        phone_half_yearly = 0

    total_phone = phone_yearly + (phone_monthly * 12) + (phone_half_yearly * 2)

    # Housing
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Housing"')
    amount = connector.fetchall()
    housing_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Housing"')
    amount = connector.fetchall()
    housing_monthly = amount[0][0]

    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Housing"')
    amount = connector.fetchall()
    housing_half_yearly = amount[0][0]

    if housing_yearly is None:
        housing_yearly = 0

    if housing_monthly is None:
        housing_monthly = 0

    if housing_half_yearly is None:
        housing_half_yearly = 0

    total_housing = housing_yearly + (housing_monthly * 12) + (housing_half_yearly * 2)

    # Streaming
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Streaming"')
    amount = connector.fetchall()
    streaming_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Streaming"')
    amount = connector.fetchall()
    streaming_monthly = amount[0][0]

    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Streaming"')
    amount = connector.fetchall()
    streaming_half_yearly = amount[0][0]

    if streaming_yearly is None:
        streaming_yearly = 0

    if streaming_monthly is None:
        streaming_monthly = 0

    if streaming_half_yearly is None:
        streaming_half_yearly = 0

    total_streaming = streaming_yearly + (streaming_monthly * 12) + (streaming_half_yearly * 2)

    # Storage
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "Storage"')
    amount = connector.fetchall()
    storage_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "Storage"')
    amount = connector.fetchall()
    storage_monthly = amount[0][0]

    connector.execute(
        'SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "Storage"')
    amount = connector.fetchall()
    storage_half_yearly = amount[0][0]

    if storage_yearly is None:
        storage_yearly = 0

    if storage_monthly is None:
        storage_monthly = 0

    if storage_half_yearly is None:
        storage_half_yearly = 0

    total_storage = storage_yearly + (storage_monthly * 12) + (storage_half_yearly * 2)

    # App
    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Yearly" AND category = "App"')
    amount = connector.fetchall()
    app_yearly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Monthly" AND category = "App"')
    amount = connector.fetchall()
    app_monthly = amount[0][0]

    connector.execute('SELECT SUM(Amount) FROM subscriptiontracker WHERE cycle = "Half Yearly" AND category = "App"')
    amount = connector.fetchall()
    app_half_yearly = amount[0][0]

    if app_yearly is None:
        app_yearly = 0

    if app_monthly is None:
        app_monthly = 0

    if app_half_yearly is None:
        app_half_yearly = 0

    total_app = app_yearly + (app_monthly * 12) + (app_half_yearly * 2)

    label['text'] = f"""Number of Subscriptions = {total_sub[0][0]}
    
Amount Paid for Subscriptions Yearly = Rs.{total_amount}/-

Amount Paid for Subscriptions Monthly = Rs.{math.floor(monthly_amount / 12)}/-

Category Wise Amount Per Year:
1. Music = Rs.{total_music}/-
2. Streaming = Rs.{total_streaming}/-
3. Housing = Rs.{total_housing}/-
4. Gaming = Rs.{total_gaming}/-
5. Phone/Internet = Rs.{total_phone}/-
6. Storage = Rs.{total_storage}/-
7. App = Rs. {total_app}/-
"""

    menu_button = tk.Button(bottom_frame, bd=3, text="Menu", font=(
        'Helvetica', 13, 'bold'), bg='#00bcd4', fg='#fffcfc', command=menu)
    menu_button.place(relx=0.75, rely=0.05, relwidth=0.2, relheight=0.1)


def subscriptions_manager():
    # StringVar and DoubleVar variables
    global desc
    desc = tk.StringVar()
    global amount
    amount = tk.DoubleVar()
    global category
    category = tk.StringVar(value='Music')
    global MoP
    MoP = tk.StringVar(value='Cash')
    global cycle
    cycle = tk.StringVar(value='Yearly')

    tk.Label(root, text='SUBSCRIPTIONS TRACKER', font=('Helvetica',
                                                       20, 'bold'), bg=button_bg, fg='red').place(x=0, rely=0,
                                                                                                  relheight=0.08,
                                                                                                  relwidth=1)

    # Frames
    global data_entry_frame
    data_entry_frame = tk.Frame(root, bg=entry_frame_bg)
    data_entry_frame.place(x=0, rely=0.06, relheight=0.95, relwidth=0.25)

    buttons_frame = tk.Frame(root, bg=buttons_frame_bg)
    buttons_frame.place(relx=0.25, rely=0.06, relwidth=0.75, relheight=0.21)

    tree_frame = tk.Frame(root)
    tree_frame.place(relx=0.25, rely=0.26, relwidth=0.75, relheight=0.74)

    # Data Entry Frame
    tk.Label(data_entry_frame, text='Date (MM/DD/YY) :',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=50)

    global date
    date = DateEntry(data_entry_frame,
                     date=datetime.datetime.now().date(), font=entry_font)
    date.place(x=160, y=50)

    tk.Label(data_entry_frame, text='Description           :',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=100)
    tk.Entry(data_entry_frame, font=entry_font,
             width=31, text=desc).place(x=10, y=130)

    tk.Label(data_entry_frame, text='Category\t             :',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=230)

    dd1 = tk.OptionMenu(data_entry_frame, category, *
    ['Music', 'Streaming', 'Housing', 'Gaming', 'Phone/Internet', 'Storage', 'App'])
    dd1.place(x=155, y=230)
    dd1.configure(width=11, font=entry_font)

    tk.Label(data_entry_frame, text='Amount\t             :',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=180)
    tk.Entry(data_entry_frame, font=entry_font,
             width=14, text=amount).place(x=160, y=180)

    tk.Label(data_entry_frame, text='Mode of Payment:',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=310)
    dd2 = tk.OptionMenu(data_entry_frame, MoP, *
    ['Cash', 'Cheque', 'Credit Card', 'Debit Card', 'Paytm', 'UPI', 'Razorpay'])
    dd2.place(x=160, y=305)
    dd2.configure(width=10, font=entry_font)

    tk.Label(data_entry_frame, text='Bill Cycle:',
             font=lbl_font, bg=entry_frame_bg, fg='white').place(x=10, y=350)
    dd3 = tk.OptionMenu(data_entry_frame, cycle, *
    ['Yearly', 'Monthly', 'Half Yearly'])
    dd3.place(x=160, y=350)
    dd3.configure(width=10, font=entry_font)

    tk.Button(data_entry_frame, text='Add Subscription', command=add_subscriptions, font=btn_font, width=30,
              bg=button_bg, fg='red').place(x=10, y=395)

    # Buttons' Frame
    tk.Button(buttons_frame, text='Delete Subscription', font=btn_font, width=25,
              bg=button_bg, fg='red', command=remove_subscriptions).place(x=30, y=5)

    tk.Button(buttons_frame, text='Clear Selection', font=btn_font, width=25, bg=button_bg, fg='red',
              command=clear_fields).place(x=335, y=5)

    tk.Button(buttons_frame, text='Delete All Subscriptions', font=btn_font,
              width=25, bg=button_bg, fg='red', command=remove_all_subscriptions).place(x=640, y=5)

    tk.Button(buttons_frame, text='View Subscription\'s Details', font=btn_font, width=25, bg=button_bg,
              fg='red', command=view_subscription_details).place(x=30, y=65)

    tk.Button(buttons_frame, text='Edit Selected Subscription', command=edit_subscription,
              font=btn_font, width=25, bg=button_bg, fg='red', ).place(x=335, y=65)

    tk.Button(buttons_frame, text='Menu', font=btn_font, width=25, bg=button_bg, fg='red',
              command=menu).place(x=640, y=65)

    # Treeview Frame
    global table
    table = ttk.Treeview(tree_frame, selectmode=tk.BROWSE, columns=(
        'ID', 'Date', 'Bill Date', 'Category', 'Description', 'Amount', 'Mode of Payment', 'Bill Cycle'))

    X_Scroller = tk.Scrollbar(table, orient=tk.HORIZONTAL, command=table.xview)
    Y_Scroller = tk.Scrollbar(table, orient=tk.VERTICAL, command=table.yview)
    X_Scroller.pack(side=tk.BOTTOM, fill=tk.X)
    Y_Scroller.pack(side=tk.RIGHT, fill=tk.Y)

    table.config(yscrollcommand=Y_Scroller.set, xscrollcommand=X_Scroller.set)

    table.heading('ID', text='S.no', anchor=tk.CENTER)
    table.heading('Date', text='Date', anchor=tk.CENTER)
    table.heading('Bill Date', text='Bill Date', anchor=tk.CENTER)
    table.heading('Category', text='Category', anchor=tk.CENTER)
    table.heading('Description', text='Description', anchor=tk.CENTER)
    table.heading('Amount', text='Amount', anchor=tk.CENTER)
    table.heading('Mode of Payment', text='Mode of Payment', anchor=tk.CENTER)
    table.heading('Bill Cycle', text='Bill Cycle', anchor=tk.CENTER)

    table.column('#0', width=0, stretch=tk.NO)
    table.column('#1', width=50, stretch=tk.NO)
    table.column('#2', width=95, stretch=tk.NO)  # Date column
    table.column('#3', width=150, stretch=tk.NO)  # Payee column
    table.column('#4', width=135, stretch=tk.NO)  # Title column
    table.column('#5', width=250, stretch=tk.NO)  # Amount column
    table.column('#6', width=125, stretch=tk.NO)  # Mode of Payment column
    table.column('#7', width=125, stretch=tk.NO)  # Mode of Payment column
    table.column('#8', width=125, stretch=tk.NO)  # Mode of Payment column

    table.place(relx=0, y=0, relheight=1, relwidth=1)

    # Lists all subscriptions in the table as soon as the window opens
    list_all_subscriptions()

    # Finalizing the GUI window
    root.update()
    root.mainloop()


# Main Menu
def menu():
    background_image = tk.PhotoImage(file='back.png')
    background_label = tk.Label(root, image=background_image)
    background_label.place(relheight=1, relwidth=1)

    global title
    title = tk.Label(root, bd=3, text="Subscription Tracker",
                     bg='#00bcd4', fg='#1769aa', font=('Helvetica', 20, 'bold'))
    title.place(relx=0.32, rely=0.02, relheight=0.065, relwidth=0.4)

    global frame
    frame = tk.Frame(root, bd=3, bg='#1769aa')
    frame.place(relx=0.1, rely=0.12, relheight=0.08, relwidth=0.8)

    global sub_menu
    sub_menu = tk.Label(frame, bd=0, font=('Helvetica', 15, 'bold'),
                        anchor='nw', justify='center', fg='#fffcfc', bg='#1769aa', text="MENU")
    sub_menu.place(relx=0.48, rely=0.11, relheight=0.79, relwidth=0.12)

    global bottom_frame
    bottom_frame = tk.Frame(root, bg='#00bcd4')
    bottom_frame.place(relx=0.1, rely=0.25, relheight=0.65, relwidth=0.8)

    global label
    label = tk.Label(bottom_frame, bd=2, bg='#1769aa', font=(
        'Helvetica', 13, 'bold'), anchor='nw', justify='left', fg='#00827e')
    label.place(relx=0.05, rely=0.05, relheight=0.9, relwidth=0.9)

    add_sub = tk.Button(bottom_frame, text="Subscriptions Manager", bd=2, bg='#00bcd4',
                        fg='#fffcfc', font=('Helvetica', 14, 'bold'), command=subscriptions_manager)
    add_sub.place(relx=0.1, rely=0.1, relheight=0.15, relwidth=0.8)

    subscription_report = tk.Button(bottom_frame, text="Subscriptions Report", bd=2,
                                    bg='#00bcd4', fg='#fffcfc', font=('Helvetica', 14, 'bold'),
                                    command=subscription_reports)
    subscription_report.place(relx=0.1, rely=0.3, relheight=0.15, relwidth=0.8)

    remainders = tk.Button(bottom_frame, text="Remainders", bd=2, bg='#00bcd4', fg='#fffcfc', font=(
        'Helvetica', 14, 'bold'), command=remainder)
    remainders.place(relx=0.1, rely=0.5, relheight=0.15, relwidth=0.8)

    exit = tk.Button(bottom_frame, text="Exit", bd=2, bg='#00bcd4', fg='#fffcfc', font=(
        'Helvetica', 14, 'bold'), command=close_app)
    exit.place(relx=0.1, rely=0.7, relheight=0.15, relwidth=0.8)

    root.mainloop()


# Closes the App.
def close_app():
    root.destroy()


# Backgrounds anf Fonts
entry_frame_bg = '#00bcd4'
buttons_frame_bg = '#00bcd4'
button_bg = '#11e9f5'

lbl_font = ('Georgia', 13)
entry_font = 'Times 13 bold'
btn_font = ('Helvetica bold', 13)

# Initializing the GUI window
root = tk.Tk()
root.title('Subscription Tracker')
root.geometry('1200x600')
# root.resizable(0, 0)

# Calls the Menu Main on start of program
menu()
