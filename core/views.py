from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.contrib.auth.decorators import login_required
from .models import UserProfile, RecentTrain
from django.contrib.auth.models import User
from .config import crowd_api, live_track_api
import requests
import json
import logging
import time
import datetime
from pytz import timezone

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

API_KEY = live_track_api

def welcome(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            validator = EmailValidator()
            validator(email)
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid email or password.'})
        except ValidationError:
            return JsonResponse({'success': False, 'message': 'Invalid email format.'})
    elif request.method == 'POST':
        email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            validator = EmailValidator()
            validator(email)
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        except ValidationError:
            messages.error(request, 'Invalid email format.')
    return render(request, 'welcome.html')

def register_user(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        phone = request.POST.get('phone', '').strip()

        try:
            validator = EmailValidator()
            validator(email)
            if password == confirm_password:
                if User.objects.filter(email=email).exists():
                    messages.error(request, 'Email already registered.')
                    return render(request, 'register_user.html')
                else:
                    user = User.objects.create_user(username=email, email=email, password=password)
                    user.first_name = full_name.split()[0] if ' ' in full_name else full_name
                    user.last_name = full_name.split()[1] if len(full_name.split()) > 1 else ''
                    user.save()
                    profile = UserProfile.objects.create(user=user, phone=phone)
                    messages.success(request, 'Registration successful! Please log in.')
                    return redirect('welcome')
            else:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'register_user.html')
        except ValidationError:
            messages.error(request, 'Invalid email format.')
            return render(request, 'register_user.html')
    return render(request, 'register_user.html')

@login_required
def dashboard(request):
    context = {}
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.debug(f"Received POST request with data: {request.POST}")
        headers = {
            'x-rapidapi-key': API_KEY,
            'x-rapidapi-host': 'indian-railway-irctc.p.rapidapi.com'
        }
        max_retries = 3

        def make_api_request(url, params=None, attempt=0):
            try:
                response = requests.get(url, headers=headers, params=params)
                logger.debug(f"Attempt {attempt + 1} - URL: {url}, Params: {params}")
                logger.debug(f"Response status: {response.status_code}, Content: {response.text}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.debug(f"Parsed JSON data: {data}")
                        if data.get('status', {}).get('result') == 'success' and data.get('error') is None:
                            return data
                        return {'error': data.get('status', {}).get('message', {}).get('message', 'API request failed')}
                    except json.JSONDecodeError:
                        return {'error': 'Invalid response format from API'}
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (2 ** attempt)
                        logger.debug(f"Rate limit hit. Retrying after {wait_time} seconds...")
                        time.sleep(wait_time)
                        return make_api_request(url, params, attempt + 1)
                    return {'error': 'Rate limit exceeded. Please try again later.'}
                elif response.status_code == 403:
                    return {'error': 'Access forbidden. Please check API subscription or key.'}
                elif response.status_code == 404:
                    return {'error': 'API endpoint not found or resource unavailable'}
                return {'error': f'Failed to fetch data (Status: {response.status_code}) - {response.text}'}
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                return {'error': 'Network error occurred'}

        if 'trainNumber' in request.POST:
            train_number = request.POST.get('trainNumber').strip()
            logger.debug(f"Fetching live status for train: {train_number}")
            if not train_number.isdigit():
                logger.debug(f"Invalid train number detected: {train_number}")
                return JsonResponse({'live_status': {'error': 'Train number must be numeric'}})
            logger.debug(f"Validated train number: {train_number}")

            current_date = datetime.datetime.now().strftime('%Y%m%d')  # e.g., 20250420
            url = f"https://indian-railway-irctc.p.rapidapi.com/api/trains/v1/train/status"
            params = {
                'train_number': train_number,
                'departure_date': current_date,
                'isH5': 'true',
                'client': 'web'
            }
            result = make_api_request(url, params)
            logger.debug(f"Train Live Status Result: {result}")
            if result.get('error') is None:
                logger.debug(f"Entering live_status construction block for result: {result}")
                try:
                    logger.debug("Starting try block execution")
                    body = result.get('body', {})
                    logger.debug(f"Body extracted: {body}")
                    stations = body.get('stations', [])
                    logger.debug(f"Stations extracted: {stations}")
                    current_station_code = body.get('current_station', 'Not available')
                    logger.debug(f"Current station code: {current_station_code}")
                    current_station_obj = next((s for s in stations if s.get('stationCode') == current_station_code), {})
                    logger.debug(f"Current station object: {current_station_obj}")
                    live_status = {
                        'number': train_number,
                        'current_station_code': current_station_code,
                        'current_station_name': current_station_obj.get('stationName', 'Not available'),
                        'day_count': current_station_obj.get('dayCount', 'Not available'),
                        'status': body.get('train_status_message', 'Not available'),
                        'last_updated': body.get('time_of_availability', body.get('server_timestamp', 'Not available')),
                        'distance_covered': current_station_obj.get('distance', 'Not available'),
                        'arrival_time': current_station_obj.get('actual_arrival_time', current_station_obj.get('arrivalTime', 'Not available')),
                        'departure_time': current_station_obj.get('actual_departure_time', current_station_obj.get('departureTime', 'Not available')),
                        'platform': current_station_obj.get('expected_platform', 'Not available'),
                        'stations': [
                            {
                                'stationCode': s.get('stationCode', 'Not available'),
                                'stationName': s.get('stationName', 'Not available'),
                                'arrivalTime': s.get('actual_arrival_time', s.get('arrivalTime', 'Not available')),
                                'departureTime': s.get('actual_departure_time', s.get('departureTime', 'Not available')),
                                'distance': s.get('distance', 'Not available'),
                                'expected_platform': s.get('expected_platform', 'Not available')
                            } for s in stations
                        ]
                    }
                    logger.debug(f"Constructed live_status: {live_status}")
                    # Store recent train data in the database
                    RecentTrain.objects.update_or_create(
                        number=train_number,
                        defaults={
                            'current_station_name': live_status['current_station_name'],
                            'status': live_status['status'],
                            'last_updated': datetime.datetime.fromisoformat(live_status['last_updated'].replace('Z', '+00:00')) if 'Z' in live_status['last_updated'] else datetime.datetime.now()
                        }
                    )
                    return JsonResponse({'live_status': live_status})
                except Exception as e:
                    logger.error(f"Exception in live_status construction: {e}")
                    return JsonResponse({'live_status': {'error': str(e)}})
            logger.debug(f"Error in result: {result.get('error', 'No error')}")
            return JsonResponse({'live_status': {'error': result.get('error', 'Unknown error')}})

    return render(request, 'dashboard.html', context)

@login_required
def crowd_info(request):
    def make_api_request(url, attempt=0):
        max_retries = 3
        try:
            response = requests.get(url)
            logger.debug(f"Attempt {attempt + 1} - URL: {url}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Parsed JSON data: {data}")
                    if data.get('ResponseCode') == "200" and data.get('Status') == "SUCCESS":
                        return data
                    return {'error': data.get('Status', 'API request failed')}
                except json.JSONDecodeError:
                    return {'error': 'Invalid response format from API'}
            elif response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = 10 * (2 ** attempt)
                    logger.debug(f"Rate limit hit. Retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
                    return make_api_request(url, attempt + 1)
                return {'error': 'Rate limit exceeded. Please try again later.'}
            return {'error': f'Failed to fetch data (Status: {response.status_code})'}
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {'error': 'Network error occurred'}

    ist = timezone('Asia/Kolkata')
    current_time = datetime.datetime.now(ist)
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

    if request.method == 'POST':
        station_code = request.POST.get('station_code', '').strip().upper()
        if not station_code:
            return render(request, 'crowd_info.html', {'error': 'Station code is required.', 'current_time': current_time_str})

        url = f"http://indianrailapi.com/api/v2/AllTrainOnStation/apikey/{crowd_api}/StationCode/{station_code}"
        result = make_api_request(url)
        logger.debug(f"Trains at Station Result for {station_code}: {result}")

        if result.get('error') is None:
            trains = result.get('Trains', [])
            train_count = 0

            # Filter trains within ±15 minutes window
            for train in trains:
                arrival_time_str = train.get('ArrivalTime', '00:00:00')
                departure_time_str = train.get('DepartureTime', '00:00:00')

                try:
                    arrival_time = datetime.datetime.strptime(arrival_time_str, '%H:%M:%S').replace(
                        year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=ist
                    )
                    departure_time = datetime.datetime.strptime(departure_time_str, '%H:%M:%S').replace(
                        year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=ist
                    )
                except ValueError:
                    logger.warning(f"Invalid time format for train at {station_code}, skipping train")
                    continue

                time_window = 15 * 60  # 15 minutes in seconds
                time_diff_arrival = abs((arrival_time - current_time).total_seconds())
                time_diff_departure = abs((departure_time - current_time).total_seconds())

                if time_diff_arrival <= time_window or time_diff_departure <= time_window:
                    train_count += 1

            # Determine crowd density with new thresholds
            hour = current_time.hour
            is_night = 23 <= hour or hour < 5
            if is_night:
                density = 'Low'
            else:
                if train_count > 10:
                    density = 'High'
                elif train_count > 5:
                    density = 'Medium'
                else:
                    density = 'Low'

            crowd_data = {'station': station_code, 'density': density, 'train_count': train_count}
            return render(request, 'crowd_info.html', {'crowd_data': crowd_data, 'current_time': current_time_str})
        else:
            return render(request, 'crowd_info.html', {'error': result.get('error', 'Unknown error'), 'current_time': current_time_str})

    return render(request, 'crowd_info.html', {'current_time': current_time_str})

def logout_view(request):
    logout(request)
    return redirect('welcome')

@login_required
def recents(request):
    recent_trains = RecentTrain.objects.all().order_by('-last_updated')[:5]
    context = {'recent_trains': recent_trains}
    return render(request, 'recents.html', context)

@login_required
def coach_layout(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if 'trainNumber' in request.POST:
            train_number = request.POST.get('trainNumber').strip()
            logger.debug(f"Fetching coach layout for train: {train_number}")
            if not train_number.isdigit():
                logger.debug(f"Invalid train number detected: {train_number}")
                return JsonResponse({'coach_layout': {'error': 'Train number must be numeric'}})
            logger.debug(f"Validated train number: {train_number}")

            url = f"http://indianrailapi.com/api/v2/CoachLayout/apikey/{crowd_api}/TrainNumber/{train_number}"
            headers = {
                'X-Requested-With': 'XMLHttpRequest'
            }
            max_retries = 3

            def make_api_request(url, attempt=0):
                try:
                    response = requests.get(url, headers=headers)
                    logger.debug(f"Attempt {attempt + 1} - URL: {url}")
                    logger.debug(f"Response status: {response.status_code}, Content: {response.text}")
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.debug(f"Parsed JSON data: {data}")
                            if data.get('ResponseCode') == "200" and data.get('Status') == "SUCCESS":
                                return data
                            return {'error': data.get('Status', 'API request failed')}
                        except json.JSONDecodeError:
                            return {'error': 'Invalid response format from API'}
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            wait_time = 10 * (2 ** attempt)
                            logger.debug(f"Rate limit hit. Retrying after {wait_time} seconds...")
                            time.sleep(wait_time)
                            return make_api_request(url, attempt + 1)
                        return {'error': 'Rate limit exceeded. Please try again later.'}
                    return {'error': f'Failed to fetch data (Status: {response.status_code}) - {response.text}'}
                except requests.RequestException as e:
                    logger.error(f"Request failed: {e}")
                    return {'error': 'Network error occurred'}

            result = make_api_request(url)
            logger.debug(f"Coach Layout Result: {result}")
            if result.get('error') is None:
                return JsonResponse({'coach_layout': result})
            return JsonResponse({'coach_layout': {'error': result.get('error', 'Unknown error')}})

    return render(request, 'coach_layout.html')

@login_required
def trains_at_station(request):
    logger.debug("Entering trains_at_station view")
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        station_code = request.POST.get('stationCode', '').strip().upper()
        logger.debug(f"Received station code: {station_code}")
        if not station_code:
            logger.debug("Station code is empty")
            return JsonResponse({'trains': {'error': 'Station code is required'}})

        url = f"http://indianrailapi.com/api/v2/AllTrainOnStation/apikey/{crowd_api}/StationCode/{station_code}"
        logger.debug(f"Constructed API URL: {url}")
        max_retries = 3

        def make_api_request(url, attempt=0):
            try:
                response = requests.get(url)
                logger.debug(f"Attempt {attempt + 1} - URL: {url}")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('ResponseCode') == "200" and data.get('Status') == "SUCCESS":
                            return data
                        return {'error': data.get('Status', 'API request failed')}
                    except json.JSONDecodeError:
                        return {'error': 'Invalid response format from API'}
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = 10 * (2 ** attempt)
                        logger.debug(f"Rate limit hit. Retrying after {wait_time} seconds...")
                        time.sleep(wait_time)
                        return make_api_request(url, attempt + 1)
                    return {'error': 'Rate limit exceeded. Please try again later.'}
                return {'error': f'Failed to fetch data (Status: {response.status_code})'}
            except requests.RequestException as e:
                logger.error(f"Request failed: {e}")
                return {'error': 'Network error occurred'}

        result = make_api_request(url)
        logger.debug(f"Trains at Station Result: {result}")
        if result.get('error') is None:
            current_time = datetime.datetime.now(timezone('Asia/Kolkata'))
            start_time = current_time - datetime.timedelta(minutes=15)
            end_time = current_time + datetime.timedelta(minutes=30)
            filtered_trains = [
                train for train in result.get('Trains', [])
                if datetime.datetime.strptime(train.get('ArrivalTime', '00:00:00'), '%H:%M:%S').replace(year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=timezone('Asia/Kolkata')).replace(second=0, microsecond=0) >= start_time.replace(second=0, microsecond=0) and
                datetime.datetime.strptime(train.get('ArrivalTime', '00:00:00'), '%H:%M:%S').replace(year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=timezone('Asia/Kolkata')).replace(second=0, microsecond=0) <= end_time.replace(second=0, microsecond=0) or
                datetime.datetime.strptime(train.get('DepartureTime', '00:00:00'), '%H:%M:%S').replace(year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=timezone('Asia/Kolkata')).replace(second=0, microsecond=0) >= start_time.replace(second=0, microsecond=0) and
                datetime.datetime.strptime(train.get('DepartureTime', '00:00:00'), '%H:%M:%S').replace(year=current_time.year, month=current_time.month, day=current_time.day, tzinfo=timezone('Asia/Kolkata')).replace(second=0, microsecond=0) <= end_time.replace(second=0, microsecond=0)
            ]
            logger.debug(f"Filtered trains: {filtered_trains}")
            return JsonResponse({'trains': filtered_trains})
        logger.debug(f"Error in result: {result.get('error', 'No error')}")
        return JsonResponse({'trains': {'error': result.get('error', 'Unknown error')}})

    logger.debug("Rendering trains_at_station.html")
    return render(request, 'trains_at_station.html')