from sqlalchemy.orm import Session

from app.models import Item, Slot
from app.schemas import ItemBulkEntry, ItemCreate


# -----------------------------
# Add Single Item
# -----------------------------
def add_item_to_slot(db: Session, slot_id: str, data: ItemCreate) -> Item:
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise ValueError("slot_not_found")

    if data.quantity <= 0:
        raise ValueError("invalid_quantity")

    if slot.current_item_count + data.quantity > slot.capacity:
        raise ValueError("capacity_exceeded")

    item = Item(
        name=data.name,
        price=data.price,
        slot_id=slot_id,
        quantity=data.quantity,
    )

    db.add(item)
    slot.current_item_count += data.quantity

    db.commit()
    db.refresh(item)

    return item


# -----------------------------
# Bulk Add Items
# -----------------------------
def bulk_add_items(
    db: Session, slot_id: str, entries: list[ItemBulkEntry]
) -> int:
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise ValueError("slot_not_found")

    if not entries:
        raise ValueError("empty_bulk_request")

    total_quantity = 0

    for e in entries:
        if e.quantity <= 0:
            raise ValueError("invalid_quantity")
        total_quantity += e.quantity

    if slot.current_item_count + total_quantity > slot.capacity:
        raise ValueError("capacity_exceeded")

    added_count = 0

    for e in entries:
        item = Item(
            name=e.name,
            price=e.price,
            slot_id=slot_id,
            quantity=e.quantity,
        )
        db.add(item)
        slot.current_item_count += e.quantity
        added_count += 1

    db.commit()

    return added_count


# -----------------------------
# List Items in Slot
# -----------------------------
def list_items_by_slot(db: Session, slot_id: str) -> list[Item]:
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise ValueError("slot_not_found")

    return list(slot.items)


# -----------------------------
# Get Item by ID
# -----------------------------
def get_item_by_id(db: Session, item_id: str) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ValueError("item_not_found")
    return item


# -----------------------------
# Update Item Price
# -----------------------------
def update_item_price(db: Session, item_id: str, price: int) -> None:
    if price <= 0:
        raise ValueError("invalid_price")

    item = get_item_by_id(db, item_id)

    item.price = price
    db.commit()


# -----------------------------
# Remove Item Quantity / Full Remove
# -----------------------------
def remove_item_quantity(
    db: Session,
    slot_id: str,
    item_id: str,
    quantity: int | None,
) -> None:
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise ValueError("slot_not_found")

    item = (
        db.query(Item)
        .filter(Item.id == item_id, Item.slot_id == slot_id)
        .first()
    )
    if not item:
        raise ValueError("item_not_found")

    # Remove partial quantity
    if quantity is not None:

        if quantity <= 0:
            raise ValueError("invalid_quantity")

        if quantity > item.quantity:
            raise ValueError("quantity_exceeds_stock")

        item.quantity -= quantity
        slot.current_item_count -= quantity

        if item.quantity == 0:
            db.delete(item)

    # Remove entire item
    else:
        slot.current_item_count -= item.quantity
        db.delete(item)

    # Final safety check
    if slot.current_item_count < 0:
        raise ValueError("slot_count_corrupted")

    db.commit()
# -----------------------------
# Bulk Remove Items
# -----------------------------
def bulk_remove_items(
    db: Session,
    slot_id: str,
    item_ids: list[str] | None,
) -> None:
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise ValueError("slot_not_found")

    # 🔥 CASE 1 — Clear entire slot
    if item_ids is None:
        for item in slot.items:
            db.delete(item)

        slot.current_item_count = 0
        db.commit()
        return

    # 🔥 CASE 2 — Remove specific items
    if not item_ids:
        raise ValueError("empty_bulk_request")

    for item_id in item_ids:
        item = (
            db.query(Item)
            .filter(Item.id == item_id, Item.slot_id == slot_id)
            .first()
        )

        if not item:
            raise ValueError("item_not_found")

        slot.current_item_count -= item.quantity
        db.delete(item)

    if slot.current_item_count < 0:
        raise ValueError("slot_count_corrupted")

    db.commit()
