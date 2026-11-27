import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from db import get_connection
from PIL import Image, ImageTk
from pathlib import Path
from tkinter import simpledialog
from decimal import Decimal



def show_catalog(user):

    cart = {}

    def apply_filters():
        load_products(
            search_entry.get(),
            category_box.get(),
            sort_box.get()
        )

    def show_cart():

        def change_quantity():
            selected = cart_tree.selection()

            if not selected:
                messagebox.showwarning("Внимание", "Выьерите товар")
                return
            values = cart_tree.item(selected[0], 'values')
            product_id = int(values[0])

            connection = get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute('select quantity from product_items where id = %s', (product_id,))

            product = cursor.fetchone()

            cursor.close()
            connection.close()

            if product is None or product["quantity"] <= 0:
                messagebox.showwarning("Внимание", "Товар недоступен")
                return

            quantity = simpledialog.askinteger(
                "Количество",
                "Введите новое количество",
                initialvalue=cart[product_id]["quantity"],
                minvalue=1,
                maxvalue=product["quantity"],
                parent=cart_window
                )

            if quantity is None:
                return

            cart[product_id]["quantity"] = quantity

            refresh_cart()

        def remove_from_cart():
            selected = cart_tree.selection()

            if not selected:
                messagebox.showwarning("Внимание", "Выьерите товар")
                return

            values = cart_tree.item(selected[0], "values")
            product_id = int(values[0])

            del cart[product_id]


            refresh_cart()

        def refresh_cart():
            for item in cart_tree.get_children():
                cart_tree.delete(item)
            total = Decimal("0.00")

            for product_id, product in cart.items():
                subtotal = product["price"] * product["quantity"]

                cart_tree.insert("", "end", values=(
                    product_id,
                    product["name"],
                    product["modification"],
                    product["price"],
                    product["quantity"],
                    subtotal

                ))
                total += subtotal
            total_label.config(text=f"Итого: {total:.2f} руб.")


        cart_window = tk.Toplevel(root)
        cart_window.title("ТехноСфера - Корзина")
        cart_window.geometry("800x450")

        cart_window.transient(root)
        cart_window.grab_set()

        cart_tree = ttk.Treeview(
            cart_window,
            columns=("id", "name", "modification", "price", "quantity", "total"),
            show="headings",
            selectmode="browse"
        )
        cart_tree.heading("id", text="ID")
        cart_tree.heading("name", text="Название")
        cart_tree.heading("modification", text="Модификация")
        cart_tree.heading("price", text="Цена")
        cart_tree.heading("quantity", text="Количество")
        cart_tree.heading("total", text="Стоимость")

        cart_tree.column("id", width=40)
        cart_tree.column("name", width=170)
        cart_tree.column("modification", width=120)
        cart_tree.column("price",width=100)
        cart_tree.column("quantity", width=100)
        cart_tree.column("total", width=120)
        cart_tree.pack(fill='both', expand=True, padx=10, pady=10)

        total_label = tk.Label(
            cart_window,
            text="Итого: 0 руб.",
            font=("Arial", 14, "bold")
        )
        total_label.pack(pady=10)

        button_frame = tk.Frame(cart_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Изменить количество", command=change_quantity).pack(side='left', padx=5)
        tk.Button(button_frame, text="Удалить товар", command=remove_from_cart).pack(side='left', padx=5)
        tk.Button(button_frame, text="Закрыть корзину", command=cart_window.destroy).pack(side='left', padx=5)




        refresh_cart()

    def add_to_cart():
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар")
            return
        values = tree.item(selected[0], "values")
        product_item_id = int(values[0])
        name = values[1]
        modification = values[3]
        price = Decimal(str(values[4]))
        stock = int(values[5])

        alredy_added = 0
        if product_item_id in cart:
            alredy_added = cart[product_item_id]["quantity"]
        available = stock - alredy_added
        if available <= 0:
            messagebox.showwarning("Внимание", "Недостаточно товара")
            return
        quantity = simpledialog.askinteger(
            "Количество",
            "Сколько товаров добавить?",
            minvalue=1,
            maxvalue=available
        )

        if quantity is None:
            return

        if product_item_id in cart:
            cart[product_item_id]["quantity"] += quantity
        else:
            cart[product_item_id] = {
                "name": name,
                "modification": modification,
                "price": price,
                "quantity": quantity
            }
        messagebox.showinfo("Успешно", "Товар добавлен в корзину")

        print(cart)

    def select_product(event):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], 'values')
        product_item_id = int(values[0])
        info_lable.config(text=f"{values[1]}\nМодификация: {values[3]}\nЦена: {values[4]}\nВ наличии: {values[5]}")

        query = f"""
        select products.image
        from product_items
        join products on product_items.product_id = products.id
        where product_items.id = %s
        """
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (product_item_id,))
        product = cursor.fetchone()

        cursor.close()
        connection.close()


        path = Path(__file__).resolve().parent / product["image"]
        image = Image.open(path)
        image.thumbnail((180, 180))

        photo = ImageTk.PhotoImage(image)
        image_lable.config(image=photo)
        image_lable.image = photo

    for widget in root.winfo_children():
        widget.destroy()

    root.title("ТехноСфера - Каталог")
    root.geometry("1000x600")

    tk.Label(root, text="Каталог товаров").pack()

    if user is None:
        tk.Label(root, text="Вы вошли как гость").pack()
    else:
        tk.Label(root, text=f"Пользователь: {user['name']}").pack()
        tk.Label(root, text=f"Роль: {user['role']}").pack()
    if user is not None:
        filter_frame = tk.Frame(root)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Поиск:").pack(side="left")

        search_entry = tk.Entry(filter_frame)
        search_entry.pack(side='left', padx=5)

        tk.Label(filter_frame, text="Категория:").pack(side="left")

        category_box = ttk.Combobox(
            filter_frame,
            values=["Все категории", "Ноутбуки", "Мыши", "Видеокарты", "Диски", "ОЗУ"],
            state="readonly"
        )
        category_box.current(0)
        category_box.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Сортировка:").pack(side='left')

        sort_box = ttk.Combobox(filter_frame, values=["Без сортировки", "Сначала дешевле", "Сначала дороже"], state="readonly")
        sort_box.current(0)
        sort_box.pack(side="left", padx=5)

        search_button = tk.Button(filter_frame, text="Применить", command=apply_filters)
        search_button.pack(side='left', padx=5)



    tree = ttk.Treeview(
            root,
            columns=("id", "name", "category", "modification", "price", "quantity"),
            show="headings",
            selectmode="browse"
        )
    tree.heading("id", text="ID")
    tree.heading("name", text="Название")
    tree.heading("category", text="Категория")
    tree.heading("modification", text="Модификация")
    tree.heading("price", text="Цена")
    tree.heading("quantity", text="Остаток")

    tree.column("id", width=50)
    tree.column("quantity", width=50)

    tree.bind("<<TreeviewSelect>>", select_product)


    tree.pack(fill='both', expand=True, padx=10, pady=10)

    info_frame = tk.Frame(root)
    info_frame.pack(fill='x', padx=10, pady=10)

    image_lable = tk.Label(info_frame)
    image_lable.pack(side='left', padx=10)

    info_lable = tk.Label(info_frame, text="Выберите товар", justify='left', font=("Arial", 12))
    info_lable.pack(side='left', padx=15)

    if user is not None:
        tk.Button(
            info_frame,
            text="Добавить в корцизу",
            command=add_to_cart
        ).pack(side="left", padx=15)
        tk.Button(info_frame, text="Открыть корзину", command=show_cart).pack(side="right", padx=10)

    def load_products(search="", category="Все категории", sort="Без сортировки"):
        query="""
        select product_items.id, products.name, products.category, modifications.value as modification, products.price, product_items.quantity
        from product_items
        join products on product_items.product_id = products.id
        join modifications on product_items.modification_id = modifications.id
        where products.name like %s
        """
        params = [f"%{search}%"]
        if category != "Все категории":
            query += " and products.category = %s"
            params.append(category)
        if sort == "Сначала дешевле":
            query += " order by products.price ASC"
        elif sort == "Сначала дороже":
            query += " order by products.price DESC"
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        tree_list = cursor.fetchall()

        for item in tree.get_children():
            tree.delete(item)
        info_lable.config(text="Выберите товар")
        image_lable.config(image='')
        image_lable.image = None
        for product in tree_list:
            tree.insert("", 'end', values=(product["id"], product["name"], product["category"], product["modification"], product["price"], product["quantity"]))
        cursor.close()
        connection.close()
    load_products()





def authorization():
    login = entry_login.get()
    print(login)
    if login == '':
        messagebox.showwarning("Внимание", "Введите логин!")
    else:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
    select users.id, users.name, roles.name as role
    from users
    join roles on users.role_id = roles.id
    where login = %s
    """
        cursor.execute(query, (login,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user is None:
            messagebox.showerror("Ошибка", "Пользователь не найден")
        else:
            messagebox.showinfo("Успешно", f"Добро пожаловать, {user['name']} - {user['role']}")
            show_catalog(user)

def guest():
    messagebox.showinfo("Добро пожаловать", "Вы вошли как гость")
    show_catalog(None)





root = tk.Tk()
root.geometry("400x300")
root.title("ТехноСфера - Авторизация")
lable_welcome = tk.Label(root, text='Добро пожаловать а ТехноСферу')
lable_welcome.pack()
lable_login = tk.Label(root, text="Введите логин:")
lable_login.pack()
entry_login = tk.Entry(root)
entry_login.pack()
button_auth= tk.Button(root, text="Войти", command=authorization)
button_auth.pack()
button_guest= tk.Button(root, text="Войти как гость", command=guest)
button_guest.pack()
root.mainloop()
