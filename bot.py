import os
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 653654882


# =========================
# DATABASE
# =========================

def init_db():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            product TEXT,
            price INTEGER,
            status TEXT
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM products")

    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            [
                ("سرویس ۱ ماهه", 100000, "مدت سرویس: ۳۰ روز"),
                ("سرویس ۳ ماهه", 250000, "مدت سرویس: ۹۰ روز"),
                ("سرویس ۶ ماهه", 450000, "مدت سرویس: ۱۸۰ روز"),
            ],
        )

    conn.commit()
    conn.close()


# =========================
# PRODUCTS
# =========================

def get_products():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, price, description FROM products ORDER BY id"
    )

    products = cursor.fetchall()
    conn.close()

    return products


def get_product(product_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name, price, description
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    )

    product = cursor.fetchone()
    conn.close()

    return product


def add_product(name, price, description):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, price, description)
        VALUES (?, ?, ?)
        """,
        (name, price, description),
    )

    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,),
    )

    conn.commit()
    conn.close()


# =========================
# ORDERS
# =========================

def create_order(user_id, username, product, price):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO orders
        (user_id, username, product, price, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            username,
            product,
            price,
            "در انتظار پرداخت",
        ),
    )

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id


def get_user_orders(user_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, product, price, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    orders = cursor.fetchall()
    conn.close()

    return orders


def get_all_orders():
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, user_id, username, product, price, status
        FROM orders
        ORDER BY id DESC
        """
    )

    orders = cursor.fetchall()
    conn.close()

    return orders


def get_order(order_id):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, user_id, username, product, price, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    )

    order = cursor.fetchone()
    conn.close()

    return order


def update_order_status(order_id, status):
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (status, order_id),
    )

    conn.commit()
    conn.close()


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🛒 محصولات",
                callback_data="products"
            )
        ],
        [
            InlineKeyboardButton(
                "📦 خریدهای من",
                callback_data="orders"
            )
        ],
        [
            InlineKeyboardButton(
                "🎧 پشتیبانی",
                callback_data="support"
            )
        ],
    ]

    await update.message.reply_text(
        "سلام 👋\n\n"
        "به فروشگاه خوش اومدی 🛍️\n\n"
        "یک گزینه رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# SHOW PRODUCTS
# =========================

async def show_products(query):

    products = get_products()
    keyboard = []

    for product in products:

        product_id, name, price, description = product

        keyboard.append([
            InlineKeyboardButton(
                f"🔐 {name} — {price:,} تومان",
                callback_data=f"product_{product_id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 بازگشت",
            callback_data="back"
        )
    ])

    await query.edit_message_text(
        "🛍️ محصولات فروشگاه\n\n"
        "محصول موردنظر رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# USER BUTTONS
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user

    if query.data == "products":

        await show_products(query)

    elif query.data.startswith("product_"):

        product_id = int(query.data.split("_")[1])
        product = get_product(product_id)

        if not product:
            await query.edit_message_text(
                "❌ محصول پیدا نشد."
            )
            return

        product_id, name, price, description = product

        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 ثبت سفارش",
                    callback_data=f"buy_{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 برگشت",
                    callback_data="products",
                )
            ],
        ]

        await query.edit_message_text(
            f"📦 {name}\n\n"
            f"💰 قیمت: {price:,} تومان\n\n"
            f"{description}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data.startswith("buy_"):

        product_id = int(query.data.split("_")[1])
        product = get_product(product_id)

        if not product:
            await query.edit_message_text(
                "❌ محصول پیدا نشد."
            )
            return

        product_id, name, price, description = product

        order_id = create_order(
            user.id,
            user.username or "",
            name,
            price,
        )

        await query.edit_message_text(
            f"✅ سفارش ثبت شد!\n\n"
            f"🧾 شماره سفارش: #{order_id}\n"
            f"📦 محصول: {name}\n"
            f"💰 مبلغ: {price:,} تومان\n"
            f"📌 وضعیت: در انتظار پرداخت\n\n"
            "💳 درگاه پرداخت در مرحله بعد اضافه می‌شود."
        )

    elif query.data == "orders":

        orders = get_user_orders(user.id)

        if not orders:

            text = (
                "📦 خریدهای من\n\n"
                "هنوز سفارشی ثبت نکردی."
            )

        else:

            text = "📦 خریدهای من\n\n"

            for order in orders:

                order_id, product, price, status = order

                text += (
                    f"🧾 سفارش #{order_id}\n"
                    f"📦 {product}\n"
                    f"💰 {price:,} تومان\n"
                    f"📌 وضعیت: {status}\n\n"
                )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "support":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back"
                )
            ]
        ]

        await query.edit_message_text(
            "🎧 پشتیبانی\n\n"
            "برای ارتباط با پشتیبانی پیام خودت رو ارسال کن.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "back":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 محصولات",
                    callback_data="products"
                )
            ],
            [
                InlineKeyboardButton(
                    "📦 خریدهای من",
                    callback_data="orders"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎧 پشتیبانی",
                    callback_data="support"
                )
            ],
        ]

        await query.edit_message_text(
            "🏠 منوی اصلی",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================
# ADMIN
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )

        return

    keyboard = [
        [
            InlineKeyboardButton(
                "📦 سفارش‌ها",
                callback_data="admin_orders"
            )
        ],
        [
            InlineKeyboardButton(
                "🛍️ محصولات",
                callback_data="admin_products"
            )
        ],
        [
            InlineKeyboardButton(
                "➕ افزودن محصول",
                callback_data="admin_add"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ حذف محصول",
                callback_data="admin_delete"
            )
        ],
    ]

    await update.message.reply_text(
        "👑 پنل مدیریت\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# ADMIN BUTTONS
# =========================

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:

        await query.edit_message_text(
            "⛔ دسترسی غیرمجاز."
        )

        return

    # -------------------------
    # ORDERS
    # -------------------------

    if query.data == "admin_orders":

        orders = get_all_orders()

        if not orders:

            text = "📦 هنوز سفارشی ثبت نشده."

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin"
                    )
                ]
            ]

        else:

            text = "📦 سفارش‌ها\n\n"
            keyboard = []

            for order in orders[:20]:

                order_id, user_id, username, product, price, status = order

                text += (
                    f"🧾 #{order_id}\n"
                    f"👤 @{username or 'بدون username'}\n"
                    f"📦 {product}\n"
                    f"💰 {price:,} تومان\n"
                    f"📌 {status}\n\n"
                )

                keyboard.append([
                    InlineKeyboardButton(
                        f"⚙️ مدیریت سفارش #{order_id}",
                        callback_data=f"manage_order_{order_id}",
                    )
                ])

            keyboard.append([
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin"
                )
            ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # MANAGE ORDER
    # -------------------------

    elif query.data.startswith("manage_order_"):

        order_id = int(
            query.data.split("_")[2]
        )

        order = get_order(order_id)

        if not order:

            await query.edit_message_text(
                "❌ سفارش پیدا نشد."
            )

            return

        order_id, user_id, username, product, price, status = order

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 پرداخت موفق",
                    callback_data=f"status_{order_id}_paid",
                )
            ],
            [
                InlineKeyboardButton(
                    "📤 ارسال به مشتری",
                    callback_data=f"send_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ در انتظار پرداخت",
                    callback_data=f"status_{order_id}_pending",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 سفارش‌ها",
                    callback_data="admin_orders"
                )
            ],
        ]

        await query.edit_message_text(
            f"🧾 سفارش #{order_id}\n\n"
            f"👤 @{username or 'بدون username'}\n"
            f"📦 {product}\n"
            f"💰 {price:,} تومان\n"
            f"📌 وضعیت فعلی: {status}\n\n"
            "گزینه موردنظر رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # PAYMENT SUCCESS
    # -------------------------

    elif query.data.startswith("status_"):

        parts = query.data.split("_")

        order_id = int(parts[1])
        status_type = parts[2]

        if status_type == "paid":

            new_status = "پرداخت موفق"

        else:

            new_status = "در انتظار پرداخت"

        order = get_order(order_id)

        if not order:

            await query.edit_message_text(
                "❌ سفارش پیدا نشد."
            )

            return

        update_order_status(
            order_id,
            new_status
        )

        user_id = order[1]

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🔔 بروزرسانی سفارش\n\n"
                    f"🧾 سفارش #{order_id}\n"
                    f"📦 {order[3]}\n"
                    f"📌 وضعیت جدید: {new_status}"
                ),
            )

        except Exception:
            pass

        keyboard = [
            [
                InlineKeyboardButton(
                    "📤 ارسال به مشتری",
                    callback_data=f"send_{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 سفارش‌ها",
                    callback_data="admin_orders"
                )
            ],
        ]

        await query.edit_message_text(
            f"✅ وضعیت سفارش #{order_id} تغییر کرد.\n\n"
            f"📌 {new_status}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # SEND TO CUSTOMER
    # -------------------------

    elif query.data.startswith("send_"):

        order_id = int(
            query.data.split("_")[1]
        )

        order = get_order(order_id)

        if not order:

            await query.edit_message_text(
                "❌ سفارش پیدا نشد."
            )

            return

        context.user_data["sending_order_id"] = order_id

        await query.edit_message_text(
            f"📤 ارسال سفارش #{order_id}\n\n"
            f"📦 محصول: {order[3]}\n"
            f"👤 مشتری: @{order[2] or 'بدون username'}\n\n"
            "حالا متن، کد، لینک یا اطلاعات سرویس "
            "که باید برای مشتری ارسال شود را در یک پیام بفرست."
        )

    # -------------------------
    # PRODUCTS
    # -------------------------

    elif query.data == "admin_products":

        products = get_products()

        text = "🛍️ محصولات فعلی\n\n"

        for product in products:

            product_id, name, price, description = product

            text += (
                f"#{product_id} — {name}\n"
                f"💰 {price:,} تومان\n\n"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 پنل مدیریت",
                    callback_data="admin"
                )
            ]
        ]

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # ADD PRODUCT
    # -------------------------

    elif query.data == "admin_add":

        context.user_data["admin_action"] = "add_product"

        await query.edit_message_text(
            "➕ افزودن محصول\n\n"
            "این فرمت رو در یک پیام بفرست:\n\n"
            "نام محصول | قیمت | توضیحات\n\n"
            "مثال:\n"
            "سرویس ۱۲ ماهه | 800000 | مدت سرویس ۳۶۵ روز"
        )

    # -------------------------
    # DELETE PRODUCT
    # -------------------------

    elif query.data == "admin_delete":

        products = get_products()
        keyboard = []

        for product in products:

            product_id, name, price, description = product

            keyboard.append([
                InlineKeyboardButton(
                    f"🗑️ {name}",
                    callback_data=f"delete_{product_id}",
                )
            ])

        keyboard.append([
            InlineKeyboardButton(
                "🔙 پنل مدیریت",
                callback_data="admin"
            )
        ])

        await query.edit_message_text(
            "🗑️ محصول موردنظر رو انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # DELETE PRODUCT
    # -------------------------

    elif query.data.startswith("delete_"):

        product_id = int(
            query.data.split("_")[1]
        )

        delete_product(product_id)

        await query.edit_message_text(
            "✅ محصول حذف شد.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 پنل مدیریت",
                        callback_data="admin"
                    )
                ]
            ]),
        )

    # -------------------------
    # ADMIN HOME
    # -------------------------

    elif query.data == "admin":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📦 سفارش‌ها",
                    callback_data="admin_orders"
                )
            ],
            [
                InlineKeyboardButton(
                    "🛍️ محصولات",
                    callback_data="admin_products"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ افزودن محصول",
                    callback_data="admin_add"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ حذف محصول",
                    callback_data="admin_delete"
                )
            ],
        ]

        await query.edit_message_text(
            "👑 پنل مدیریت",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================
# ADMIN TEXT
# =========================

async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    # -------------------------
    # SEND PRODUCT TO CUSTOMER
    # -------------------------

    if "sending_order_id" in context.user_data:

        order_id = context.user_data["sending_order_id"]

        order = get_order(order_id)

        if not order:

            context.user_data.pop(
                "sending_order_id",
                None
            )

            await update.message.reply_text(
                "❌ سفارش پیدا نشد."
            )

            return

        user_id = order[1]
        delivery_text = update.message.text

        try:

            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"📦 تحویل سفارش #{order_id}\n\n"
                    f"{delivery_text}\n\n"
                    "🙏 ممنون از خرید شما."
                ),
            )

            update_order_status(
                order_id,
                "تحویل شد"
            )

            await update.message.reply_text(
                f"✅ سفارش #{order_id} با موفقیت برای مشتری ارسال شد.\n\n"
                "📌 وضعیت: تحویل شد"
            )

        except Exception:

            await update.message.reply_text(
                "❌ ارسال به مشتری انجام نشد.\n"
                "ممکنه مشتری ربات رو بلاک کرده باشه."
            )

        context.user_data.pop(
            "sending_order_id",
            None
        )

        return

    # -------------------------
    # ADD PRODUCT
    # -------------------------

    if context.user_data.get("admin_action") != "add_product":
        return

    parts = update.message.text.split("|", 2)

    if len(parts) != 3:

        await update.message.reply_text(
            "❌ فرمت اشتباهه.\n\n"
            "نام محصول | قیمت | توضیحات"
        )

        return

    name = parts[0].strip()
    price_text = parts[1].strip()
    description = parts[2].strip()

    try:

        price = int(price_text)

    except ValueError:

        await update.message.reply_text(
            "❌ قیمت باید عدد باشه."
        )

        return

    add_product(
        name,
        price,
        description
    )

    context.user_data["admin_action"] = None

    await update.message.reply_text(
        f"✅ محصول اضافه شد!\n\n"
        f"📦 {name}\n"
        f"💰 {price:,} تومان"
    )


# =========================
# MAIN
# =========================

def main():

    init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_buttons,
            pattern=r"^(admin|admin_orders|admin_products|admin_add|admin_delete|delete_.*|manage_order_.*|status_.*|send_.*)$"
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            buttons
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            admin_text
        )
    )

    print(
        "فروشگاه + پنل مدیریت + تحویل دستی روشن شد..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
