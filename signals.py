from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Request, Notification, Item, Transaction

@receiver(post_save, sender=Request)
def handle_request_status_change(sender, instance, created, **kwargs):
    # When a 'Borrow' or 'Buy' request is APPROVED
    if instance.status == 'APPROVED':
        item = instance.item
        if item.item_type == 'BORROW':
            item.status = 'ON_LOAN'
        else:
            item.status = 'SOLD'
        item.save()
        
        # Create a Transaction record automatically
        Transaction.objects.create(
            item=item,
            buyer_borrower=instance.requester,
            owner=item.owner,
            transaction_type=item.item_type,
            amount=item.price if item.price else 0.00,
            is_completed=(item.item_type == 'SALE')
        )
        
        # Notify the requester
        Notification.objects.create(
            user=instance.requester,
            text=f"Your request for '{item.name}' has been APPROVED!",
            link='/dashboard/'
        )

    # When a request is first Created (Status becomes 'Pending' on Item)
    if created:
        item = instance.item
        item.status = 'PENDING'
        item.save()
        
        # Notify the owner
        Notification.objects.create(
            user=item.owner,
            text=f"New request for your item: {item.name}",
            link='/dashboard/'
        )
