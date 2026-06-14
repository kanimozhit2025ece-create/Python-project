from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max
from django.db.models.functions import TruncHour, TruncMonth
from django.http import JsonResponse
from .models import Item, Category, Request, Notification, SearchQuery, Transaction, Review, Profile
from .forms import UserRegisterForm, ItemForm, RequestForm, ReviewForm
from django.utils import timezone
from datetime import timedelta

def home(request):
    categories = Category.objects.all()
    latest_items = Item.objects.filter(status='AVAILABLE').order_by('-created_at')[:8]
    # Trending Now (from SearchQuery)
    trending_terms = list(SearchQuery.objects.values('term').annotate(count=Count('id')).order_by('-count')[:5])
    if not trending_terms:
        # Defaults if no searches yet
        trending_terms = [
            {'term': 'Textbooks'},
            {'term': 'Lab Gear'},
            {'term': 'Laptops'},
            {'term': 'Dorm Decor'},
            {'term': 'Calculators'}
        ]
    
    # Top Rated Sellers (Annotated with deal counts)
    top_sellers = Profile.objects.filter(rating__gt=0).annotate(
        deal_count=Count('user__transactions_as_owner')
    ).order_by('-rating', '-deal_count')[:4]
    
    # Marketplace Pulse (Community Stats)
    items_reused = Transaction.objects.filter(is_completed=True).count()
    # Fallback for fresh DB
    if items_reused == 0: items_reused = 12 # Mock for demo
    
    total_saved = Transaction.objects.filter(is_completed=True).aggregate(total=Avg('amount'))['total'] or 0
    if total_saved == 0: total_saved = 450 # Mock for demo
    
    # Top Testimonials (Recent 5-star reviews)
    top_testimonials = Review.objects.filter(score=5).order_by('-created_at')[:3]
    if not top_testimonials:
        top_testimonials = [
            {
                'evaluator': {'username': 'Alex P.'}, 
                'comment': 'SCARE has saved me so much on Bio gear!', 
                'message': '', 
                'evaluator__profile__department': 'Biology',
                'item__owner__profile__department': 'Biology',
                'requester': {'username': 'Alex P.'}
            },
            {
                'evaluator': {'username': 'Sarah M.'}, 
                'comment': 'The campus pickup is super convenient and safe.', 
                'message': '', 
                'evaluator__profile__department': 'Engineering',
                'item__owner__profile__department': 'Engineering',
                'requester': {'username': 'Sarah M.'}
            },
            {
                'evaluator': {'username': 'James K.'}, 
                'comment': 'Found my Calc textbook in minutes. Highly recommend!', 
                'message': '', 
                'evaluator__profile__department': 'Math',
                'item__owner__profile__department': 'Math',
                'requester': {'username': 'James K.'}
            }
        ]

    # Trending in Department/Major (for logged in users)
    dept_items = []
    if request.user.is_authenticated and request.user.profile.department:
        dept_items = Item.objects.filter(
            owner__profile__department=request.user.profile.department,
            status='AVAILABLE'
        ).exclude(owner=request.user)[:4]

    return render(request, 'marketplace/home.html', {
        'categories': categories,
        'latest_items': latest_items,
        'trending_terms': trending_terms,
        'top_sellers': top_sellers,
        'dept_items': dept_items,
        'pulse': {
            'reused': items_reused,
            'saved': total_saved
        },
        'testimonials': top_testimonials
    })

def search_results(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    item_type = request.GET.get('type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    condition = request.GET.get('condition')
    location = request.GET.get('location')
    availability = request.GET.get('availability', 'available')

    items = Item.objects.all()
    
    if query:
        SearchQuery.objects.create(
            user=request.user if request.user.is_authenticated else None,
            term=query.lower(),
            category=Category.objects.filter(id=category_id).first() if category_id else None
        )
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    
    if category_id: items = items.filter(category_id=category_id)
    if item_type: items = items.filter(item_type=item_type)
    if min_price: items = items.filter(price__gte=min_price)
    if max_price: items = items.filter(price__lte=max_price)
    if condition: items = items.filter(condition=condition)
    if location: items = items.filter(location=location)
    if availability == 'available': items = items.filter(status='AVAILABLE')

    return render(request, 'marketplace/search_results.html', {
        'items': items,
        'query': query,
        'categories': Category.objects.all(),
        'conditions': Item.CONDITION_CHOICES,
        'locations': Item.LOCATION_CHOICES
    })

def quick_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    data = {
        'name': item.name,
        'description': item.description,
        'price': str(item.price) if item.price else "Free/Negotiable",
        'image': item.image.url,
        'category': str(item.category),
        'condition': item.get_condition_display(),
        'location': item.get_location_display(),
        'owner': item.owner.username,
        'rating': str(item.owner.profile.rating),
        'type': item.item_type
    }
    return JsonResponse(data)

def search_api(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    
    items = Item.objects.filter(status='AVAILABLE')
    if query:
        items = items.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        items = items.filter(category_id=category_id)
        
    results = []
    for item in items[:5]: # Limit to top 5 for dropdown
        results.append({
            'id': item.id,
            'name': item.name,
            'price': str(item.price) if item.price else "Free",
            'image': item.image.url if item.image else "",
            'category': str(item.category),
            'type': item.item_type
        })
    return JsonResponse({'results': results})

def notification_count_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'count': 0})
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        if item.owner == request.user:
            messages.error(request, "You cannot request your own item!")
            return redirect('item_detail', pk=pk)
            
        form = RequestForm(request.POST)
        if form.is_valid():
            new_request = form.save(commit=False)
            new_request.item = item
            new_request.requester = request.user
            new_request.save()
            
            messages.success(request, "Request sent to the owner!")
            return redirect('dashboard')
    else:
        form = RequestForm()
        
    return render(request, 'marketplace/item_detail.html', {'item': item, 'form': form})

@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, f'Item "{item.name}" listed successfully!')
            return redirect('dashboard')
    else:
        form = ItemForm()
    return render(request, 'marketplace/add_item.html', {'form': form})

@login_required
def dashboard(request):


    # 1. Overview Tab
    active_listings = Item.objects.filter(owner=request.user, status='AVAILABLE')
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # 2. Inventory Tab
    all_my_items = Item.objects.filter(owner=request.user)
    
    # 3. Request Manager Tab
    incoming_requests = Request.objects.filter(item__owner=request.user).order_by('-created_at')
    
    # 4. Borrowing History Tab
    my_active_borrows = Transaction.objects.filter(buyer_borrower=request.user, is_completed=False)
    # Add countdowns (calculated in template or here)
    
    return render(request, 'marketplace/dashboard.html', {
        'active_listings': active_listings,
        'notifications': notifications,
        'all_my_items': all_my_items,
        'incoming_requests': incoming_requests,
        'active_borrows': my_active_borrows,
        'item_form': ItemForm() # For inventory tab modal
    })

@login_required
def insights(request):
    # Bar Chart: Most Searched Categories
    cat_stats = SearchQuery.objects.values('category__name').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Line Graph: Daily Transaction Volume (Last 24 Hours)
    last_24_hours = timezone.now() - timedelta(hours=24)
    trans_stats = Transaction.objects.filter(
        start_date__gte=last_24_hours
    ).annotate(
        hour=TruncHour('start_date')
    ).values('hour').annotate(count=Count('id')).order_by('hour')

    # 1. Price Trends (Last 6 Months: Books vs Electronics)
    six_months_ago = timezone.now() - timedelta(days=180)
    price_trends = Transaction.objects.filter(
        start_date__gte=six_months_ago,
        item__category__name__in=['Books', 'Electronics']
    ).annotate(
        month=TruncMonth('start_date')
    ).values('month', 'item__category__name').annotate(
        avg_price=Avg('amount')
    ).order_by('month')

    # 2. Top Categories (Listed vs Sold)
    target_cats = ['Books', 'Lab Gear', 'Electronics']
    cat_comparison = []
    for cat_name in target_cats:
        listed = Item.objects.filter(category__name=cat_name, status='AVAILABLE').count()
        sold = Item.objects.filter(category__name=cat_name, status='SOLD').count()
        cat_comparison.append({'name': cat_name, 'listed': listed, 'sold': sold})

    # 3. Inventory Breakdown
    inventory = {
        'sell': Item.objects.filter(item_type='SALE', status='AVAILABLE').count(),
        'lend': Item.objects.filter(item_type='BORROW', status='AVAILABLE').count(),
        'borrow': Item.objects.filter(status='ON_LOAN').count(),
    }
    inventory['total'] = inventory['sell'] + inventory['lend'] + inventory['borrow']

    return render(request, 'marketplace/insights.html', {
        'cat_stats': cat_stats,
        'trans_stats': trans_stats,
        'price_trends': price_trends,
        'cat_comparison': cat_comparison,
        'inventory': inventory
    })

@login_required
def approve_request(request, request_id):
    item_request = get_object_or_404(Request, id=request_id, item__owner=request.user)
    item_request.status = 'APPROVED'
    item_request.save()
    # signal handles status updates and transaction creation
    messages.success(request, f"Request for {item_request.item.name} Approved!")
    return redirect('/dashboard/?celebrate=true')

@login_required
def reject_request(request, request_id):
    item_request = get_object_or_404(Request, id=request_id, item__owner=request.user)
    item_request.status = 'REJECTED'
    item_request.save()
    # update item status back to available
    item = item_request.item
    item.status = 'AVAILABLE'
    item.save()
    messages.info(request, "Request rejected.")
    return redirect('dashboard')

@login_required
def confirm_return(request, transaction_id):
    trans = get_object_or_404(Transaction, id=transaction_id, owner=request.user)
    trans.is_completed = True
    trans.end_date = timezone.now()
    trans.save()
    
    item = trans.item
    item.status = 'AVAILABLE'
    item.save()
    
    messages.success(request, "Return confirmed. Item is now available again!")
    return redirect('dashboard')

@login_required
def submit_rating(request, transaction_id):
    trans = get_object_or_404(Transaction, id=transaction_id)
    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment')
        
        # Who is rating who?
        if request.user == trans.owner:
            rated_user = trans.buyer_borrower
        else:
            rated_user = trans.owner
            
        Review.objects.create(
            transaction=trans,
            evaluator=request.user,
            rated_user=rated_user,
            score=score,
            comment=comment
        )
        messages.success(request, "Rating submitted!")
        return redirect('dashboard')
    return redirect('dashboard')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'marketplace/register.html', {'form': form})

@login_required
def admin_stats(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied. Admins only.")
        return redirect('home')
        
    # Stats for TOP Trending Searches
    top_searches = SearchQuery.objects.values('term').annotate(
        count=Count('id'),
        last_searched=Max('timestamp')
    ).order_by('-count')[:10]
    
    # Stats for Category Demand (based on search)
    category_data = SearchQuery.objects.exclude(category__isnull=True).values('category__name').annotate(
        name=Max('category__name'),
        count=Count('id')
    ).order_by('-count')[:6]
    
    return render(request, 'marketplace/admin_stats.html', {
        'top_searches': top_searches,
        'category_data': category_data
    })
