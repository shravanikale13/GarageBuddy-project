from django.shortcuts import render, redirect
from pymongo import MongoClient
import traceback
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import json
from django.utils.safestring import mark_safe
from django.utils.dateparse import parse_date
from .models import ServiceRecord, ServiceItem


def get_service_collection():
    client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster")
    db = client["garagedb"]
    return db["services"]


def get_mongo_connection():
    """Get MongoDB connection"""
    try:
        client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster", serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client["garagedb"]
        return client, db
    except Exception as e:
        print(f"MongoDB Connection Error: {str(e)}")
        raise


@require_http_methods(["GET"])
def api_search_services(request):
    """
    API endpoint to search services by vehicle number
    GET /api/services/search/?q=MH12AB1234
    """
    try:
        query = request.GET.get('q', '').strip().upper()
        
        if not query or len(query) < 3:
            return JsonResponse({
                'status': 'error',
                'message': 'Query too short',
                'data': []
            })

        print(f"🔍 Searching services for vehicle: {query}")
        
        col = get_service_collection()
        
        # Search in MongoDB
        services = list(col.find({
            "vehicle_number": {"$regex": query, "$options": "i"}
        }).sort("service_date", -1).limit(10))
        
        # Convert MongoDB ObjectId to string
        for service in services:
            service['_id'] = str(service['_id'])
            if 'created_at' in service and isinstance(service['created_at'], str):
                service['created_at'] = service['created_at'][:10]
        
        print(f"✓ Found {len(services)} service records")
        
        return JsonResponse({
            'status': 'success',
            'data': services,
            'count': len(services)
        })

    except Exception as e:
        print(f"❌ Search error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'data': []
        })


@require_http_methods(["GET"])
def service_detail(request, service_id):
    """
    Display detailed view of a specific service record
    GET /service-detail/<service_id>/
    """
    try:
        from bson import ObjectId
        
        print(f"📖 Fetching service detail: {service_id}")
        
        col = get_service_collection()
        service = col.find_one({"_id": ObjectId(service_id)})
        
        if not service:
            messages.error(request, "Service record not found!")
            return redirect('/dashboard/')
        
        # Convert ObjectId to string
        service['_id'] = str(service['_id'])
        
        print(f"✓ Service detail retrieved: {service['vehicle_number']}")
        
        return render(request, 'service_detail.html', {
            'service': service
        })
    
    except Exception as e:
        print(f"❌ Error fetching service detail: {str(e)}")
        messages.error(request, f"Error loading service: {str(e)}")
        return redirect('/dashboard/')


@require_http_methods(["GET", "POST"])
def service(request):
    """
    GET  /service/  → render blank service record form
    POST /service/  → save to both Django DB and MongoDB with proper validation
    """
    if request.method == "POST":
        print("\n" + "="*80)
        print("🔔 SERVICE RECORD POST REQUEST RECEIVED")
        print("="*80)
        
        customer_name  = request.POST.get("customer_name", "").strip()
        mechanic_name  = request.POST.get("mechanic_name", "").strip()
        vehicle_number = request.POST.get("vehicle_number", "").strip()
        service_date   = request.POST.get("service_date", "").strip()

        print(f"Customer: {customer_name}")
        print(f"Mechanic: {mechanic_name}")
        print(f"Vehicle: {vehicle_number}")
        print(f"Date: {service_date}")

        errors = []
        if not customer_name:
            errors.append("Customer name is required.")
        if not mechanic_name:
            errors.append("Mechanic name is required.")
        if not vehicle_number:
            errors.append("Vehicle number is required.")

        parsed_date = parse_date(service_date) if service_date else None
        if not parsed_date:
            errors.append("A valid service date is required.")

        service_changes = request.POST.getlist("service_changes[]")
        service_descs   = request.POST.getlist("service_desc[]")

        print(f"\nService changes: {service_changes}")
        print(f"Service descs: {service_descs}")

        items = [
            {"order": idx, "changes": change.strip(), "description": desc.strip()}
            for idx, (change, desc) in enumerate(
                zip(service_changes, service_descs), start=1
            )
            if change.strip() or desc.strip()
        ]

        print(f"Parsed items: {items}")

        if not items:
            errors.append("Please add at least one service item.")

        if errors:
            print(f"\n❌ Validation errors: {errors}")
            for error in errors:
                messages.error(request, error)
            return render(request, "services.html")

        django_success = False
        mongo_success = False
        record = None

        try:
            print("\n📝 Saving to Django DB...")
            record = ServiceRecord.objects.create(
                customer_name=customer_name,
                mechanic_name=mechanic_name,
                vehicle_number=vehicle_number,
                service_date=parsed_date,
            )
            print(f"✓ Service record created with ID: {record.id}")
            
            service_items = ServiceItem.objects.bulk_create([
                ServiceItem(
                    record=record,
                    changes=item["changes"],
                    description=item["description"],
                    order=item["order"],
                )
                for item in items
            ])
            print(f"✓ Created {len(service_items)} service items")
            django_success = True

        except Exception as exc:
            print(f"❌ Django DB Error: {str(exc)}")
            print(traceback.format_exc())
            messages.error(request, f"❌ Failed to save service record to database: {str(exc)}")
            return render(request, "services.html")

        if django_success and record:
            try:
                print("\n📝 Saving to MongoDB...")
                mongo_doc = {
                    "django_id":      str(record.pk),
                    "customer_name":  customer_name,
                    "mechanic_name":  mechanic_name,
                    "vehicle_number": vehicle_number,
                    "service_date":   service_date,
                    "items":          items,
                    "created_at":     datetime.now().isoformat(),
                    "updated_at":     datetime.now().isoformat(),
                    "status":         "completed"
                }
                col = get_service_collection()
                result = col.insert_one(mongo_doc)
                print(f"✓ MongoDB document inserted with ID: {result.inserted_id}")

                record.mongo_id = str(result.inserted_id)
                record.save(update_fields=["mongo_id"])
                print(f"✓ Updated Django record with MongoDB ID")
                mongo_success = True

            except Exception as exc:
                print(f"⚠️ MongoDB Error: {str(exc)}")
                print(traceback.format_exc())
                print("⚠️ Service saved to local database, but MongoDB backup failed")
                mongo_success = False

        if django_success:
            print("\n✅ Service record saved successfully!")
            print("="*80 + "\n")
            
            if mongo_success:
                messages.success(
                    request,
                    f"✓ Service record for {customer_name} ({vehicle_number}) saved successfully!"
                )
            else:
                messages.success(
                    request,
                    f"✓ Service record for {customer_name} ({vehicle_number}) saved successfully! (Backup pending)"
                )
            
            return redirect("/service/")
        else:
            print("\n❌ Failed to save service record")
            print("="*80 + "\n")
            return render(request, "services.html")

    return render(request, "services.html")


# Other views remain the same (homepage, signup, adduser, login, authenticate, dashboard, failure, bill, customer, vehicle)
def homepage(request):
    return render(request, "index.html")


def signup(request):
    return render(request, "signup.html")


def adduser(request):
    sts = "failed"
    error_msg = ""
    
    if request.method == "POST":
        try:
            Fnm = request.POST.get("FName")
            ps = request.POST.get("password")
            Em = request.POST.get("Email")
            Gnm = request.POST.get("Gname")
            
            if not all([Fnm, ps, Em, Gnm]):
                sts = "failed"
                error_msg = "All fields are required"
                print("Error: Missing required fields")
            else:
                client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster")
                db = client["garagedb"]
                coll = db["signup"]
                dic = {
                    'FName': Fnm,
                    'password': ps,
                    'Email': Em,
                    'Gname': Gnm
                }
                
                coll.insert_one(dic)
                sts = "success"
                print("Data inserted successfully:", dic)
                client.close()
        except Exception as e:
            sts = "failed"
            error_msg = str(e)
            print(f"Error inserting data: {e}")
            traceback.print_exc()
    
    return render(request, "dash.html", {'status': sts, 'error': error_msg})


def login(request):
    return render(request, "login.html")


def authenticate(request):
    if request.method == "POST":
        Em = request.POST.get("Email")
        ps = request.POST.get("password")
        client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster")
        db = client["garagedb"]
        coll = db["signup"]
        user = coll.find_one({"Email": Em})
        if user:
            if user["password"] == ps:
                return redirect("/dashboard/")
            else:
                return redirect("/failure/")
        else:
            return redirect("/failure/")
    return redirect("/home/")


def dashboard(request):
    return render(request, "dash.html")


def failure(request):
    return render(request, "failure.html")


def bill(request):
    if request.method == "POST":
        try:
            client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster")
            db = client["garagedb"]
            coll = db["bill"]

            CName = request.POST.get("CName")
            Pnum = request.POST.get("Pnum")
            Vnum = request.POST.get("Vnum")

            service_names = request.POST.getlist("service_name[]")
            service_costs = request.POST.getlist("service_cost[]")

            print(f"Customer: {CName}, Phone: {Pnum}, Vehicle: {Vnum}")
            print(f"Services: {service_names}, Costs: {service_costs}")

            if not CName or not Pnum or not Vnum:
                messages.error(request, "Please fill in all customer details!")
                return redirect("/bill/")

            services = []
            total = 0

            for name, cost in zip(service_names, service_costs):
                if name and cost:
                    try:
                        cost_val = float(cost)
                        services.append({
                            "service": name,
                            "cost": cost_val
                        })
                        total += cost_val
                    except ValueError:
                        print(f"Invalid cost value: {cost}")
                        continue

            if not services:
                messages.error(request, "Please add at least one service!")
                return redirect("/bill/")

            current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

            data = {
                "customer_name": CName,
                "phone_number": Pnum,
                "vehicle_number": Vnum,
                "services": services,
                "total": total,
                "date": current_date,
                "timestamp": datetime.now()
            }

            print(f"Data to insert: {data}")

            result = coll.insert_one(data)
            print(f"Document inserted with ID: {result.inserted_id}")

            client.close()

            messages.success(request, "✓ Bill stored successfully!")
            return redirect("/bill/")

        except Exception as e:
            print(f"Error in bill view: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f"Error storing bill: {str(e)}")
            return redirect("/bill/")

    return render(request, "bill.html")


def customer(request):
    """Add New Customer View"""
    client = None
    try:
        if request.method == "POST":
            print("=" * 80)
            print("🔔 POST REQUEST RECEIVED AT /customer/")
            print("=" * 80)
            
            first_name = request.POST.get("firstName", "").strip()
            last_name = request.POST.get("lastName", "").strip()
            phone = request.POST.get("phone", "").strip()
            email = request.POST.get("email", "").strip()
            address = request.POST.get("address", "").strip()
            pincode = request.POST.get("pincode", "").strip()
            city = request.POST.get("city", "").strip()
            customer_code = request.POST.get("customerCode", "").strip()
            
            reg_no = request.POST.get("regNo", "").strip()
            make = request.POST.get("make", "").strip()
            model = request.POST.get("model", "").strip()
            year = request.POST.get("year", "").strip()
            fuel_type = request.POST.get("fuelType", "").strip()
            transmission = request.POST.get("transmission", "").strip()
            odometer = request.POST.get("odometer", "").strip()
            
            known_issues = request.POST.get("knownIssues", "").strip()
            preferences = request.POST.get("preferences", "").strip()
            waiver_agreed = request.POST.get("waiverAgreed") == "on"

            if not first_name or not last_name:
                messages.error(request, "❌ First Name and Last Name are required!")
                return redirect("/customer/")

            if not phone:
                messages.error(request, "❌ Phone number is required!")
                return redirect("/customer/")

            if not email:
                messages.error(request, "❌ Email is required!")
                return redirect("/customer/")

            if not reg_no or not make or not model or not year:
                messages.error(request, "❌ Vehicle details (Registration, Make, Model, Year) are required!")
                return redirect("/customer/")

            if not fuel_type:
                messages.error(request, "❌ Fuel Type is required!")
                return redirect("/customer/")

            if not transmission:
                messages.error(request, "❌ Transmission is required!")
                return redirect("/customer/")

            print("Attempting MongoDB connection...")
            client, db = get_mongo_connection()
            print("✓ MongoDB connection successful")
            
            coll = db["customers"]

            existing_phone = coll.find_one({"phone": phone})
            if existing_phone:
                messages.warning(request, f"⚠️ Customer with phone {phone} already exists!")
                client.close()
                return redirect("/customer/")

            existing_reg = coll.find_one({"vehicles.registration_number": reg_no})
            if existing_reg:
                messages.warning(request, f"⚠️ Vehicle {reg_no} already registered!")
                client.close()
                return redirect("/customer/")

            customer_data = {
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "customer_code": customer_code if customer_code else f"CUS-{int(datetime.now().timestamp())}",
                "phone": phone,
                "email": email,
                "address": address,
                "pincode": pincode,
                "city": city,
                "vehicles": [
                    {
                        "registration_number": reg_no,
                        "make": make,
                        "model": model,
                        "year": int(year) if year else None,
                        "fuel_type": fuel_type,
                        "transmission": transmission,
                        "odometer": int(odometer) if odometer else 0,
                        "added_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    }
                ],
                "known_issues": known_issues,
                "service_preferences": preferences,
                "waiver_agreed": waiver_agreed,
                "created_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "updated_date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "status": "active",
                "total_services": 0,
                "total_spent": 0.0,
            }

            print("Customer data prepared:")
            print(customer_data)

            print("Attempting to insert document into MongoDB...")
            result = coll.insert_one(customer_data)
            print(f"✓ Document inserted successfully with ID: {result.inserted_id}")
            
            messages.success(request, f"✓ Customer {first_name} {last_name} saved successfully!")
            print(f"✓ SUCCESS - Customer saved with ID: {result.inserted_id}")
            
            if client:
                client.close()
                print("✓ MongoDB connection closed")
            
            return redirect("/customer/")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f"❌ Error saving customer: {str(e)}")
        if client:
            try:
                client.close()
            except:
                pass
        return redirect("/customer/")

    return render(request, "customer.html")


def vehicle(request):
    """Display all vehicles from customer database"""
    try:
        client = MongoClient("mongodb+srv://shravani:mongodb913@shravicluster.1nyi3vf.mongodb.net/?appName=shravicluster")
        db = client["garagedb"]
        coll = db["customers"]
        
        customers = list(coll.find({}))
        
        vehicles_list = []
        for customer in customers:
            customer_name = customer.get("full_name", "")
            customer_id = str(customer.get("_id", ""))
            phone = customer.get("phone", "")
            
            vehicles = customer.get("vehicles", [])
            for vehicle in vehicles:
                vehicles_list.append({
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "phone": phone,
                    "registration_number": vehicle.get("registration_number", ""),
                    "make": vehicle.get("make", ""),
                    "model": vehicle.get("model", ""),
                    "year": vehicle.get("year", ""),
                    "fuel_type": vehicle.get("fuel_type", ""),
                    "odometer": vehicle.get("odometer", 0),
                    "added_date": vehicle.get("added_date", ""),
                    "status": customer.get("status", "active")
                })
        
        client.close()
        
        vehicles_json = mark_safe(json.dumps(vehicles_list))
        
        return render(request, "vehicle.html", {
            "vehicles": vehicles_json,
            "total_vehicles": len(vehicles_list)
        })
    
    except Exception as e:
        print(f"Error in vehicle view: {str(e)}")
        print(traceback.format_exc())
        return render(request, "vehicle.html", {
            "vehicles": mark_safe("[]"),
            "total_vehicles": 0,
            "error": str(e)
        })
    
    
def search_page():
    return render('search.html')