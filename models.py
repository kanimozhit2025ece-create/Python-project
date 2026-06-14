from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    department = models.CharField(max_length=100, blank=True)
    # Aggregate "Campus Trust Score"
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Item(models.Model):
    TYPE_CHOICES = (
        ('BORROW', 'To Borrow'),
        ('SALE', 'For Sale'),
    )
    CONDITION_CHOICES = (
        ('NEW', 'New'),
        ('LIKE_NEW', 'Like New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
    )
    LOCATION_CHOICES = (
        ('NORTH', 'North Campus'),
        ('SOUTH', 'South Campus'),
        ('CENTRAL', 'Central Library Area'),
        ('ELAB', 'Engineering Lab'),
        ('STUDENT_UNION', 'Student Union'),
    )
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('PENDING', 'Pending Request'),
        ('ON_LOAN', 'On Loan'),
        ('SOLD', 'Sold'),
        ('RESERVED', 'Reserved'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    image = models.ImageField(upload_to='item_images/')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='BORROW')
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='GOOD')
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='CENTRAL')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AVAILABLE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Request(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved (On Loan/Sold)'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned'),
        ('COMPLETED', 'Completed'),
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='my_requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    # Duration for borrowing
    return_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.status} Request for {self.item.name} by {self.requester.username}"

class Transaction(models.Model):
    # Tracks the actual borrow/buy event
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    buyer_borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_as_buyer')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions_as_owner')
    transaction_type = models.CharField(max_length=10, choices=Item.TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Transaction: {self.item.name} ({self.transaction_type})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    text = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    # Post-transaction rating system
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='review', null=True)
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update user's aggregate rating
        reviews = Review.objects.filter(rated_user=self.rated_user)
        avg_score = sum([r.score for r in reviews]) / len(reviews)
        profile = self.rated_user.profile
        profile.rating = avg_score
        profile.save()

class SearchQuery(models.Model):
    # Logs every user search
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    term = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Search Queries"
