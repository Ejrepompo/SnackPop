
"""PyScript-powered, event-driven interactions for the SnackPop demo."""

from datetime import date
from secrets import randbelow

from js import confirm
from pyodide.ffi import create_proxy  # type: ignore[reportMissingModuleSource]
from pyscript import document  # type: ignore[reportMissingModuleSource]


SNACKS = {
    "cookie-fries": {"name": "Cookie Fries", "price": 20, "combo_price": 18},
    "mini-pancakes": {"name": "Mini Fluffy Pancakes", "price": 25},
    "lemon-bars": {"name": "Zesty Lemon Bars", "price": 25},
    "cookie-trio": {"name": "Snackable Cookie Trio", "price": 22},
    "dipped-pretzels": {"name": "Mini Dipped Pretzels", "price": 10},
    "pretzel-rods": {"name": "Dipped Pretzel Rods", "price": 15},
}
DRINKS = {
    "classic-lemonade": {"name": "Classic lemonade", "price": 12},
    "iced-tea": {"name": "Iced tea", "price": 15},
    "fruit-juice": {"name": "Fruit juice", "price": 20},
    "bottled-water": {"name": "Bottled water", "price": 10},
}
EVENT_LOG_LIMIT = 6

cart: dict[str, dict[str, str | int]] = {}
cart_dialog = document.querySelector("#cart-dialog")
cart_items = document.querySelector("#cart-items")
cart_empty = document.querySelector("#cart-empty")
cart_total = document.querySelector("#cart-total")
cart_count = document.querySelector(".cart-count")
cart_trigger = document.querySelector(".cart-trigger")
cart_status = document.querySelector("#cart-status")
checkout_button = document.querySelector("#checkout-button")
clear_cart_button = document.querySelector("#clear-cart-button")
confirmation = document.querySelector("#order-confirmation")
event_log = document.querySelector("#event-log")
event_callbacks = []


def format_price(amount: int) -> str:
    return f"₱{amount}"


def listen(element, event_name: str, handler) -> None:
    proxy = create_proxy(handler)
    event_callbacks.append(proxy)
    element.addEventListener(event_name, proxy)


def log_event(event_type: str, description: str) -> None:
    if event_log.querySelector(".event-placeholder"):
        event_log.replaceChildren()

    entry = document.createElement("li")
    entry.textContent = f"{event_type} · {description}"
    event_log.prepend(entry)

    while event_log.children.length > EVENT_LOG_LIMIT:
        event_log.removeChild(event_log.lastElementChild)


def render_cart() -> None:
    item_count = sum(int(item["quantity"]) for item in cart.values())
    total = sum(
        int(item["price"]) * int(item["quantity"])
        for item in cart.values()
    )

    cart_items.replaceChildren()
    cart_empty.hidden = item_count != 0
    cart_total.textContent = format_price(total)
    cart_count.textContent = str(item_count)
    cart_count.setAttribute(
        "aria-label", f"{item_count} {'item' if item_count == 1 else 'items'}"
    )
    cart_trigger.setAttribute(
        "aria-label",
        f"Open snack bag, {item_count} {'item' if item_count == 1 else 'items'}",
    )
    checkout_button.disabled = item_count == 0
    clear_cart_button.hidden = item_count == 0

    for key, item in cart.items():
        row = document.createElement("li")
        row.className = "cart-line"

        copy = document.createElement("div")
        copy.className = "cart-line-copy"
        title = document.createElement("strong")
        title.textContent = str(item["name"])
        copy.append(title)

        if item["detail"]:
            detail = document.createElement("small")
            detail.textContent = str(item["detail"])
            copy.append(detail)

        line_price = document.createElement("span")
        line_price.className = "cart-line-price"
        line_price.textContent = format_price(
            int(item["price"]) * int(item["quantity"])
        )

        quantity_control = document.createElement("div")
        quantity_control.className = "quantity-control"
        quantity_control.setAttribute("role", "group")
        quantity_control.setAttribute("aria-label", f"{item['name']} quantity")

        decrease_button = document.createElement("button")
        decrease_button.type = "button"
        decrease_button.dataset.quantity = key
        decrease_button.dataset.change = "-1"
        decrease_button.setAttribute(
            "aria-label", f"Remove one {item['name']}"
        )
        decrease_button.textContent = "−"

        quantity = document.createElement("span")
        quantity.className = "quantity-value"
        quantity.textContent = str(item["quantity"])
        quantity.setAttribute("aria-label", f"Quantity {item['quantity']}")

        increase_button = document.createElement("button")
        increase_button.type = "button"
        increase_button.dataset.quantity = key
        increase_button.dataset.change = "1"
        increase_button.setAttribute("aria-label", f"Add one {item['name']}")
        increase_button.textContent = "+"

        remove_button = document.createElement("button")
        remove_button.type = "button"
        remove_button.className = "remove-button"
        remove_button.dataset.remove = key
        remove_button.textContent = "Remove"

        quantity_control.append(
            decrease_button, quantity, increase_button, remove_button
        )
        row.append(copy, line_price, quantity_control)
        cart_items.append(row)


def add_to_cart(
    key: str, name: str, price: int, event_type: str, detail: str = ""
) -> None:
    if key in cart:
        cart[key]["quantity"] = int(cart[key]["quantity"]) + 1
    else:
        cart[key] = {
            "name": name,
            "price": price,
            "detail": detail,
            "quantity": 1,
        }

    confirmation.hidden = True
    checkout_button.hidden = False
    render_cart()
    cart_status.textContent = f"{name} added to your snack bag."
    log_event(event_type, f"Added {name} ({format_price(price)}).")


def open_cart(event) -> None:
    if not cart_dialog.open:
        cart_dialog.showModal()
        log_event(str(event.type), "Opened the snack bag.")


def close_cart(event=None) -> None:
    if cart_dialog.open:
        cart_dialog.close()
        if event is not None:
            log_event(str(event.type), "Closed the snack bag.")


def handle_keydown(event) -> None:
    if event.key == "Escape" and cart_dialog.open:
        event.preventDefault()
        close_cart(event)


def handle_product_add(event) -> None:
    button = event.target.closest("button[data-add], button[data-order-now]")
    if not button:
        return

    order_now = button.hasAttribute("data-order-now")
    snack_id = str(
        button.dataset.orderNow if order_now else button.dataset.add
    )
    snack = SNACKS[snack_id]
    flavor = str(
        document.querySelector(f'[data-flavor-for="{snack_id}"]').value
    )
    add_to_cart(
        f"{snack_id}:{flavor}",
        str(snack["name"]),
        int(snack["price"]),
        str(event.type),
        flavor,
    )
    if order_now:
        open_cart(event)


def handle_filter(event) -> None:
    button = event.target.closest("button[data-filter]")
    if not button:
        return

    selected_filter = str(button.dataset.filter)
    visible_count = 0

    for card in document.querySelectorAll(".product-card"):
        categories = str(card.dataset.categories).split()
        visible = selected_filter == "all" or selected_filter in categories
        card.hidden = not visible
        visible_count += int(visible)

    for filter_button in document.querySelectorAll("[data-filter]"):
        selected = filter_button == button
        filter_button.classList.toggle("is-active", selected)
        filter_button.setAttribute("aria-pressed", str(selected).lower())

    noun = "treat" if visible_count == 1 else "treats"
    document.querySelector("#filter-status").textContent = (
        f"Showing {visible_count} {noun}."
    )
    label = str(button.textContent).strip()
    log_event("click", f"Menu filter changed to {label} ({visible_count} shown).")


def update_combo(event=None) -> None:
    snack_select = document.querySelector("#combo-snack")
    snack = SNACKS[str(snack_select.value)]
    snack_price = int(snack.get("combo_price", snack["price"]))
    drink = DRINKS[str(document.querySelector("#combo-drink").value)]
    dip = str(document.querySelector("#combo-dip").value)

    document.querySelector("#combo-snack-name").textContent = str(snack["name"])
    document.querySelector("#combo-snack-price").textContent = format_price(
        snack_price
    )
    document.querySelector("#combo-drink-name").textContent = str(drink["name"])
    document.querySelector("#combo-drink-price").textContent = format_price(
        int(drink["price"])
    )
    document.querySelector("#combo-dip-name").textContent = f"Dip: {dip}"
    document.querySelector("#combo-total").textContent = format_price(
        snack_price + int(drink["price"])
    )

    if event is not None:
        if event.currentTarget.id == "combo-snack":
            log_event("change", f"Snack selected: {snack['name']}.")
        elif event.currentTarget.id == "combo-drink":
            log_event("change", f"Drink selected: {drink['name']}.")
        else:
            log_event("change", f"Complimentary dip selected: {dip}.")


def handle_add_combo(event) -> None:
    snack_id = str(document.querySelector("#combo-snack").value)
    snack = SNACKS[snack_id]
    snack_price = int(snack.get("combo_price", snack["price"]))
    drink_id = str(document.querySelector("#combo-drink").value)
    drink = DRINKS[drink_id]
    dip = str(document.querySelector("#combo-dip").value)
    name = f"{snack['name']} snack box"
    detail = f"{drink['name']} · complimentary {dip.lower()}"

    add_to_cart(
        f"combo:{snack_id}:{drink_id}:{dip}",
        name,
        snack_price + int(drink["price"]),
        str(event.type),
        detail,
    )


def handle_cart_change(event) -> None:
    button = event.target.closest("button")
    if not button:
        return

    if button.hasAttribute("data-remove"):
        key = str(button.dataset.remove)
        removed_item = cart.pop(key, None)
        if removed_item is None:
            return

        confirmation.hidden = True
        checkout_button.hidden = False
        render_cart()
        cart_dialog.querySelector("[data-close-cart]").focus()
        cart_status.textContent = f"{removed_item['name']} removed from your bag."
        log_event(
            str(event.type), f"Removed {removed_item['name']} from the bag."
        )
        return

    if button.hasAttribute("data-quantity"):
        key = str(button.dataset.quantity)
        item = cart.get(key)
        if item is None:
            return

        change = int(button.dataset.change)
        item["quantity"] = int(item["quantity"]) + change

        if int(item["quantity"]) <= 0:
            cart.pop(key)
            confirmation.hidden = True
            checkout_button.hidden = False
            render_cart()
            cart_dialog.querySelector("[data-close-cart]").focus()
            cart_status.textContent = f"{item['name']} removed from your bag."
            log_event(
                str(event.type), f"Removed {item['name']} from the bag."
            )
            return

        confirmation.hidden = True
        checkout_button.hidden = False
        render_cart()

        for control in cart_items.querySelectorAll("[data-quantity]"):
            if (
                control.dataset.quantity == key
                and control.dataset.change == str(change)
            ):
                control.focus()
                break

        quantity = int(item["quantity"])
        noun = "item" if quantity == 1 else "items"
        cart_status.textContent = (
            f"{item['name']} quantity updated to {quantity}."
        )
        log_event(
            str(event.type),
            f"Updated {item['name']} quantity to {quantity} {noun}.",
        )


def handle_clear_cart(event) -> None:
    if not cart:
        return

    if not confirm(
        "Are you sure you want to remove all items from your snack bag?"
    ):
        return

    removed_count = sum(
        int(item["quantity"]) for item in cart.values()
    )

    cart.clear()
    confirmation.hidden = True
    checkout_button.hidden = False
    render_cart()

    cart_status.textContent = (
        f"Your snack bag has been cleared. {removed_count} items removed."
    )
    log_event(
        str(event.type),
        f"Cleared all items from the bag ({removed_count} items).",
    )


def handle_checkout(event) -> None:
    if not cart:
        return

    code = f"{randbelow(10_000):04d}"
    document.querySelector("#pickup-code").textContent = code
    confirmation.hidden = False
    checkout_button.hidden = True
    cart_status.textContent = (
        "A local demo pickup code was created. Your order has not been sent."
    )
    log_event(
        str(event.type), f"Created demo pickup code {code}; no order was sent."
    )


def handle_clear_event_log(event) -> None:
    event_log.replaceChildren()
    log_event(str(event.type), "Event log cleared.")


# Retain each Pyodide proxy so its Python callback survives after registration.
listen(cart_trigger, "click", open_cart)
listen(cart_dialog.querySelector("[data-close-cart]"), "click", close_cart)
listen(
    cart_dialog,
    "click",
    lambda event: close_cart(event) if event.target == cart_dialog else None,
)
listen(document, "keydown", handle_keydown)
listen(document.querySelector("#product-grid"), "click", handle_product_add)
listen(document.querySelector(".filter-bar"), "click", handle_filter)
listen(cart_items, "click", handle_cart_change)
listen(document.querySelector("#combo-snack"), "change", update_combo)
listen(document.querySelector("#combo-drink"), "change", update_combo)
listen(document.querySelector("#combo-dip"), "change", update_combo)
listen(document.querySelector(".add-combo"), "click", handle_add_combo)
listen(checkout_button, "click", handle_checkout)
listen(clear_cart_button, "click", handle_clear_cart)
listen(document.querySelector("#clear-event-log"), "click", handle_clear_event_log)

document.querySelector("#current-year").textContent = str(date.today().year)
document.querySelector("#pyscript-status").textContent = (
    "Python ready · browser events are connected"
)
render_cart()
update_combo()
log_event("ready", "PyScript started Python and registered event handlers.")
