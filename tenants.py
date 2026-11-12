"""
Devlancer Tenant Definitions & Automatic Seeding
Contains initial configurations for prospective holiday agency clients.
"""

from database import init_db, upsert_tenant, set_tenant_packages, get_connection

SEED_TENANTS = [
    {
        "id": "tenant_prakruthi",
        "slug": "prakruthi-holidays",
        "assistant_id": "asst_prakruthi_kammanahalli",
        "name": "Prakruthi Holidays",
        "tagline": "21+ Years of Trusted Travel in Bengaluru",
        "logo_url": "https://www.prakruthiholidays.com/logo.png",
        "website_url": "https://www.prakruthiholidays.com/",
        "primary_color": "#047857",
        "secondary_color": "#064e3b",
        "accent_color": "#f59e0b",
        "assistant_name": "Prakruthi AI Concierge",
        "welcome_message": "Namaskara! Welcome to Prakruthi Holidays 🙏 With 21+ years in Bengaluru, we specialize in stress-free **Family, Honeymoon & Senior Citizen Tours** (with caring Kannada/English tour managers & homestyle Indian meals). Where are you planning your next getaway?",
        "personality_prompt": "You are 'Prakruthi AI', the 24/7 Senior Travel Concierge for Prakruthi Holidays (Bengaluru's trusted agency on Kammanahalli Main Road). Emphasize 21+ years of expertise, senior citizen comfort, homestyle Indian meals abroad, and bilingual Kannada & English tour managers.",
        "knowledge_base": "Key Strengths: 21+ years in Bangalore, Senior Citizen tour specialist with relaxed pacing and wheelchair assistance when needed. 100% Indian meals provided abroad. Caring bilingual tour managers fluent in Kannada and English. End-to-end visa and flight support.",
        "supported_languages": "English, Kannada, Hindi",
        "contact_phone": "+91 9845370515",
        "contact_email": "mail@prakruthiholidays.com",
        "contact_address": "No. 8, 1st Floor, Sree Nanjundeshwara Complex, Kammanahalli Main Road, Bengaluru",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Singapore & Malaysia Group Tour",
                "destination": "Singapore & Malaysia",
                "duration": "6 Nights / 7 Days",
                "starting_price_inr": 120000,
                "highlights": "Universal Studios, Sentosa, Petronas Towers, Genting Highlands. Bestseller for Seniors & Families with Indian meals.",
                "category": "Fixed Departure Group Tour"
            },
            {
                "name": "Bali Tour Package",
                "destination": "Bali, Indonesia",
                "duration": "6 Nights / 7 Days",
                "starting_price_inr": 100000,
                "highlights": "Ubud, Kintamani Volcano, Uluwatu Sunset, Nusa Penida Island, Water Sports & authentic Indian dinners.",
                "category": "International Holiday"
            },
            {
                "name": "Dubai Tour Package",
                "destination": "Dubai, UAE",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 105000,
                "highlights": "Burj Khalifa 124th Floor, Desert Safari with BBQ dinner, Dhow Cruise Marina, Dubai Frame & shopping.",
                "category": "Fixed Departure Group Tour"
            },
            {
                "name": "Bangkok & Pattaya Tour",
                "destination": "Thailand",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 63000,
                "highlights": "Coral Island speedboat tour, Alcazar Show, Bangkok City Temple tour, Safari World.",
                "category": "Budget International"
            },
            {
                "name": "Vietnam Tour Package",
                "destination": "Vietnam",
                "duration": "7 Nights / 8 Days",
                "starting_price_inr": 130000,
                "highlights": "Halong Bay overnight cruise, Hanoi old quarter, Da Nang Golden Bridge, Ba Na Hills.",
                "category": "Trending International"
            },
            {
                "name": "Kashmir Paradise Tour",
                "destination": "Kashmir",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 45000,
                "highlights": "Srinagar Dal Lake Shikara, Gulmarg Gondola ride, Pahalgam Betaab Valley & houseboat stay.",
                "category": "Domestic Tour"
            }
        ]
    },
    {
        "id": "tenant_many2go",
        "slug": "many2go-holidays",
        "assistant_id": "asst_many2go_holidays",
        "name": "Many2Go Holidays",
        "tagline": "Curated Fixed Departures & Tailor-Made Getaways",
        "logo_url": "https://many2go.in/logo.png",
        "website_url": "https://many2go.in/",
        "primary_color": "#1e40af",
        "secondary_color": "#172554",
        "accent_color": "#0284c7",
        "assistant_name": "Many2Go Smart Travel Concierge",
        "welcome_message": "Hello and welcome to **Many2Go Holidays**! ✈️ Looking for an unforgettable international tour or an effortless domestic getaway? We specialize in curated fixed departures with all-inclusive pricing. What destination is on your bucket list?",
        "personality_prompt": "You are 'Many2Go Smart Concierge', representing Many2Go Holidays. Energetic, consultative, and knowledgeable about fixed group departures, flight-inclusive pricing, visa turnaround, and family vacation packages.",
        "knowledge_base": "Many2Go Holidays specializes in all-inclusive fixed group departures, Europe multi-country tours, Southeast Asia, and premium domestic holidays with flights and visa assistance.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9900112233",
        "contact_email": "info@many2go.in",
        "contact_address": "Bengaluru & Mumbai Offices",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Wonders of Europe Group Tour",
                "destination": "Switzerland, France & Italy",
                "duration": "9 Nights / 10 Days",
                "starting_price_inr": 235000,
                "highlights": "Mt. Titlis, Jungfrau, Eiffel Tower Top Level, Venice Gondola, Colosseum.",
                "category": "Premium International"
            },
            {
                "name": "Vietnam & Cambodia Explorer",
                "destination": "Vietnam & Cambodia",
                "duration": "8 Nights / 9 Days",
                "starting_price_inr": 145000,
                "highlights": "Angkor Wat, Halong Bay luxury cruise, Cu Chi tunnels, Da Nang Golden Hands bridge.",
                "category": "Fixed Departure"
            },
            {
                "name": "Baku & Azerbaijan Tour",
                "destination": "Azerbaijan",
                "duration": "4 Nights / 5 Days",
                "starting_price_inr": 72000,
                "highlights": "Flame Towers, Gobustan mud volcanoes, Ateshgah Fire Temple, Shahdag mountain resort.",
                "category": "Budget International"
            }
        ]
    },
    {
        "id": "tenant_traveolla",
        "slug": "traveolla-holidays",
        "assistant_id": "asst_traveolla_vacations",
        "name": "Traveolla Holidays",
        "tagline": "Luxury Honeymoons & Bespoke Worldwide Escapes",
        "logo_url": "https://traveolla.com/logo.png",
        "website_url": "https://traveolla.com/",
        "primary_color": "#ea580c",
        "secondary_color": "#7c2d12",
        "accent_color": "#f97316",
        "assistant_name": "Traveolla Luxury Concierge",
        "welcome_message": "Welcome to **Traveolla Holidays**! 🌅 Where luxury meets wanderlust. We curate bespoke honeymoons, private villa stays in Bali, and exotic island vacations worldwide. How may we craft your dream escape today?",
        "personality_prompt": "You are 'Traveolla Luxury Concierge', specializing in bespoke honeymoon packages, private pool villas, 5-star beachfront resorts, and romantic private transfers.",
        "knowledge_base": "Traveolla Holidays specializes in luxury couples travel, personalized itineraries, Maldives water villas, private yacht charters, and premium European honeymoons.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9888877777",
        "contact_email": "concierge@traveolla.com",
        "contact_address": "Indiranagar, Bengaluru",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Maldives Overwater Villa Escape",
                "destination": "Maldives",
                "duration": "4 Nights / 5 Days",
                "starting_price_inr": 160000,
                "highlights": "Private water villa with slide, all-inclusive dine-around, speedboat transfers, sunset dolphin cruise.",
                "category": "Luxury Honeymoon"
            },
            {
                "name": "Romantic Bali Private Pool Villa",
                "destination": "Bali, Indonesia",
                "duration": "6 Nights / 7 Days",
                "starting_price_inr": 115000,
                "highlights": "Private pool villa in Seminyak & Ubud jungle resort, floating breakfast, candle-light dinner on beach.",
                "category": "Romantic Escape"
            }
        ]
    },
    {
        "id": "tenant_roameaze",
        "slug": "roameaze",
        "assistant_id": "asst_roameaze_travel",
        "name": "RoamEaze",
        "tagline": "Experiential Travel & Adventure Getaways for Millennials",
        "logo_url": "https://roameaze.com/logo.png",
        "website_url": "https://roameaze.com/",
        "primary_color": "#4f46e5",
        "secondary_color": "#312e81",
        "accent_color": "#06b6d4",
        "assistant_name": "RoamEaze AI Guide",
        "welcome_message": "Hey there! Ready to roam freely with **RoamEaze**? 🎒 We curate epic treks, offbeat backpacking adventures, and budget-friendly road trips across India and South East Asia. Where is your next adventure?",
        "personality_prompt": "You are 'RoamEaze AI Guide'. Casual, friendly, inspiring, and adventurous. Focus on treks, offbeat routes, scuba diving, hostels/boutique homestays, and exciting group road trips.",
        "knowledge_base": "RoamEaze caters to Gen-Z and millennial travelers looking for authentic experiences, Himalayan treks, Goa workations, Meghalaya living root bridges, and Thailand backpacking.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9777766666",
        "contact_email": "explore@roameaze.com",
        "contact_address": "Koramangala, Bengaluru",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Spiti Valley Road Expedition",
                "destination": "Spiti Valley, Himachal",
                "duration": "8 Nights / 9 Days",
                "starting_price_inr": 38000,
                "highlights": "Chandratal camping, Kaza, Key Monastery, world's highest post office at Hikkim, 4x4 SUV.",
                "category": "Adventure Road Trip"
            },
            {
                "name": "Meghalaya & Kaziranga Backpacking",
                "destination": "North East India",
                "duration": "6 Nights / 7 Days",
                "starting_price_inr": 42000,
                "highlights": "Double Decker root bridges, crystal clear Umngot river boating at Dawki, Kaziranga rhino safari.",
                "category": "Offbeat Explorer"
            }
        ]
    },
    {
        "id": "tenant_prestige",
        "slug": "prestige-holidays-4u",
        "assistant_id": "asst_prestige_holidays",
        "name": "Prestige Holidays 4U",
        "tagline": "Tailor-Made Luxury Worldwide & Cruise Vacations",
        "logo_url": "https://www.prestigeholidays4u.com/logo.png",
        "website_url": "https://www.prestigeholidays4u.com/",
        "primary_color": "#0f766e",
        "secondary_color": "#134e4a",
        "accent_color": "#14b8a6",
        "assistant_name": "Prestige Luxury Travel Advisor",
        "welcome_message": "Welcome to **Prestige Holidays 4U** ✨ Crafting unforgettable bespoke worldwide journeys, luxury cruises, and tailor-made European escapes. Which magnificent destination can we arrange for you?",
        "personality_prompt": "You are 'Prestige Luxury Travel Advisor', representing Prestige Holidays 4U. Refined, polite, sophisticated, highlighting ATOL-protected travel, private chauffeurs, bespoke luxury cruises, and 5-star concierge care.",
        "knowledge_base": "Prestige Holidays 4U provides bespoke luxury worldwide itineraries, Mediterranean cruises, luxury African safaris, and Caribbean private resort getaways.",
        "supported_languages": "English",
        "contact_phone": "+44 20 7946 0192",
        "contact_email": "concierge@prestigeholidays4u.com",
        "contact_address": "London & Global Travel Desks",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Greek Isles & Mediterranean Cruise",
                "destination": "Greece & Italy",
                "duration": "7 Nights / 8 Days",
                "starting_price_inr": 210000,
                "highlights": "Santorini sunset sailing, Mykonos private beach club, Athens Acropolis VIP tour, balcony cabin.",
                "category": "Luxury Cruise"
            },
            {
                "name": "Serengeti & Zanzibar Luxury Safari",
                "destination": "Tanzania & Zanzibar",
                "duration": "8 Nights / 9 Days",
                "starting_price_inr": 340000,
                "highlights": "Big 5 game drives, luxury tented lodge, private bush flight, Zanzibar white sand beachfront villa.",
                "category": "Bespoke Safari"
            }
        ]
    },
    {
        "id": "tenant_holidaytadka",
        "slug": "holidaytadka",
        "assistant_id": "asst_holidaytadka_tours",
        "name": "HolidayTadka",
        "tagline": "Adding Spicy Flavors & Value to Your Vacations",
        "logo_url": "https://holidaytadka.com/logo.png",
        "website_url": "https://holidaytadka.com/",
        "primary_color": "#dc2626",
        "secondary_color": "#991b1b",
        "accent_color": "#f87171",
        "assistant_name": "Tadka Travel Assistant",
        "welcome_message": "Namaste! Welcome to **HolidayTadka** 🌶️ Adding the perfect flavor to your family vacations! We offer budget-friendly domestic getaways and super-value international holidays with 100% transparency. Where would you like to travel?",
        "personality_prompt": "You are 'Tadka Travel Assistant' for HolidayTadka. Vibrant, friendly, value-focused. Emphasize budget transparency, no hidden charges, family-friendly hotel locations, and customizable Indian meals.",
        "knowledge_base": "HolidayTadka offers affordable packages for Kerala, Himachal, Andaman, Dubai, Thailand, and Goa with trusted driver-guides and verified 3/4-star hotels.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9123456789",
        "contact_email": "booking@holidaytadka.com",
        "contact_address": "Delhi & Mumbai Branch Offices",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Kerala Backwaters & Munnar Hills",
                "destination": "Kerala, India",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 28000,
                "highlights": "Munnar tea gardens, Alleppey deluxe private houseboat with all meals, Kochi Dutch Palace.",
                "category": "Domestic Bestseller"
            },
            {
                "name": "Himachal Snow & Valley Tour",
                "destination": "Shimla & Manali",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 32000,
                "highlights": "Solang Valley snow activities, Atal Tunnel, Rohtang Pass, Kufri horse riding, private sedan.",
                "category": "Domestic Holiday"
            }
        ]
    },
    {
        "id": "tenant_ekashmir",
        "slug": "ekashmir-tour-package",
        "assistant_id": "asst_ekashmir_tours",
        "name": "eKashmir Tour Package",
        "tagline": "Specialist in Heaven on Earth – Kashmir Holidays",
        "logo_url": "https://www.ekashmirtourpackage.com/logo.png",
        "website_url": "https://www.ekashmirtourpackage.com/",
        "primary_color": "#0284c7",
        "secondary_color": "#075985",
        "accent_color": "#38bdf8",
        "assistant_name": "Kashmir Valley Concierge",
        "welcome_message": "Aadab & Welcome to **eKashmir Tour Package** 🏔️ Experience Heaven on Earth! From Dal Lake luxury houseboats to Gulmarg snow gondolas and Pahalgam pine valleys, we curate authentic Kashmir experiences. How can we plan your visit?",
        "personality_prompt": "You are 'Kashmir Valley Concierge', representing eKashmir Tour Package. Warm Kashmiri hospitality, knowledgeable on local weather, Gondola phase 1 & 2 tickets, Dal Lake houseboats, Betaab valley, and saffron shopping.",
        "knowledge_base": "eKashmir Tour Package is Srinagar's premier tour operator with direct luxury houseboats on Dal Lake & Nigeen Lake, authorized Gondola ticket coordination, and heating-equipped luxury transport.",
        "supported_languages": "English, Urdu, Hindi",
        "contact_phone": "+91 9419012345",
        "contact_email": "tours@ekashmirtourpackage.com",
        "contact_address": "Boulevard Road, Dal Lake, Srinagar, Kashmir",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Heavenly Kashmir Honeymoon & Family",
                "destination": "Srinagar, Gulmarg & Pahalgam",
                "duration": "5 Nights / 6 Days",
                "starting_price_inr": 39000,
                "highlights": "1 Night Luxury Houseboat stay, Shikara ride at sunset, Gulmarg Gondola Cable Car, Aru & Betaab Valley cab.",
                "category": "Kashmir Special"
            },
            {
                "name": "Grand Kashmir & Ladakh Odyssey",
                "destination": "Kashmir & Ladakh",
                "duration": "8 Nights / 9 Days",
                "starting_price_inr": 68000,
                "highlights": "Srinagar to Leh via Kargil & Zojila Pass, Pangong Tso Lake, Nubra Valley sand dunes & double-humped camel.",
                "category": "Himalayan Expedition"
            }
        ]
    },
    {
        "id": "tenant_adventurehive",
        "slug": "adventurehive",
        "assistant_id": "asst_adventurehive_expeditions",
        "name": "AdventureHive",
        "tagline": "Thrills, Treks, Wildlife Safaris & Camping",
        "logo_url": "https://www.adventurehive.in/logo.png",
        "website_url": "https://www.adventurehive.in/",
        "primary_color": "#d97706",
        "secondary_color": "#78350f",
        "accent_color": "#fbbf24",
        "assistant_name": "AdventureHive Expedition AI",
        "welcome_message": "Welcome to **AdventureHive**! 🧗‍♂️ Craving real adrenaline? We organize Himalayan summits, white-water rafting, scuba diving in the Andamans, and deep jungle tiger safaris. What adventure are you ready to conquer?",
        "personality_prompt": "You are 'AdventureHive Expedition AI'. Dynamic, safety-conscious, passionate about the outdoors. Emphasize certified mountain guides, wilderness first aid, eco-friendly camping, and high-adrenaline activities.",
        "knowledge_base": "AdventureHive is an accredited adventure tour company specializing in certified trek leaders, Jim Corbett and Ranthambore wildlife safaris, Rishikesh rafting, and Leh biking.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9988776655",
        "contact_email": "explore@adventurehive.in",
        "contact_address": "Rishikesh & Dehradun Base Camps",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Kedarkantha Winter Snow Trek",
                "destination": "Uttarakhand Himalayas",
                "duration": "4 Nights / 5 Days",
                "starting_price_inr": 12500,
                "highlights": "12,500 ft summit climb, alpine lake Juda Ka Talab camping, certified trek leader, all equipment provided.",
                "category": "Himalayan Trek"
            },
            {
                "name": "Rishikesh White-Water & Cliff Jump",
                "destination": "Rishikesh, Uttarakhand",
                "duration": "2 Nights / 3 Days",
                "starting_price_inr": 8500,
                "highlights": "24km Marine Drive rafting, body surfing, cliff jumping, riverside luxury dome camping with bonfire.",
                "category": "Adrenaline Weekend"
            }
        ]
    },
    {
        "id": "tenant_destico",
        "slug": "destico",
        "assistant_id": "asst_destico_travel",
        "name": "Destico",
        "tagline": "Smart Group Departures & Corporate MICE Getaways",
        "logo_url": "https://destico.in/logo.png",
        "website_url": "https://destico.in/",
        "primary_color": "#2563eb",
        "secondary_color": "#1e3a8a",
        "accent_color": "#60a5fa",
        "assistant_name": "Destico Business & Leisure Concierge",
        "welcome_message": "Hello and welcome to **Destico**! 🌐 We streamline corporate offsites, reward trips, and seamless international group holidays. Looking for group booking rates or a customized itinerary?",
        "personality_prompt": "You are 'Destico Concierge'. Professional, efficient, corporate and leisure savvy. Highlight volume discounts, flight charter coordination, GST invoice support, and seamless conference arrangements.",
        "knowledge_base": "Destico handles corporate offsites and large family reunions with customized event venues, meeting spaces, team-building excursions in Dubai, Thailand, Goa, and Sri Lanka.",
        "supported_languages": "English, Hindi",
        "contact_phone": "+91 9811223344",
        "contact_email": "contact@destico.in",
        "contact_address": "Gurugram Cyber City, NCR",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Dubai MICE & Incentive Group Package",
                "destination": "Dubai, UAE",
                "duration": "4 Nights / 5 Days",
                "starting_price_inr": 88000,
                "highlights": "5-star ballroom setup, desert gala dinner with live entertainment, luxury coach transfers, GST input tax credits.",
                "category": "Corporate Offsite"
            },
            {
                "name": "Goa Beachfront Resort Retreat",
                "destination": "South Goa",
                "duration": "3 Nights / 4 Days",
                "starting_price_inr": 26000,
                "highlights": "Private beach resort buyout, cocktail dinner, team-building beach games, airport AC Volvo coaches.",
                "category": "Group Retreat"
            }
        ]
    },
    {
        "id": "tenant_trueyatri",
        "slug": "trueyatri",
        "assistant_id": "asst_trueyatri_spiritual",
        "name": "TrueYatri",
        "tagline": "Devotional Pilgrimages & Heritage Tours of Sacred India",
        "logo_url": "https://www.trueyatri.com/logo.png",
        "website_url": "https://www.trueyatri.com/",
        "primary_color": "#b45309",
        "secondary_color": "#78350f",
        "accent_color": "#f59e0b",
        "assistant_name": "TrueYatri Seva Concierge",
        "welcome_message": "Pranam and welcome to **TrueYatri** 🙏 We organize peaceful and comfortable Teerth Yatras (Char Dham, Kashi-Varanasi, Ayodhya, and South India Temples) with VIP Darshan and pure satvik meals. How may we serve your pilgrimage?",
        "personality_prompt": "You are 'TrueYatri Seva Concierge'. Respectful, devotional, caring for elderly pilgrims. Highlight VIP temple darshan, clean hygienic hotels, pure Satvik vegetarian food, and dedicated tour coordinators.",
        "knowledge_base": "TrueYatri specializes in spiritual tourism across India with helicopter darshan services in Kedarnath/Badrinath, elderly-friendly wheelchair support, and pure vegetarian food arrangements.",
        "supported_languages": "English, Hindi, Sanskrit",
        "contact_phone": "+91 9311002200",
        "contact_email": "seva@trueyatri.com",
        "contact_address": "Varanasi Ghats & New Delhi",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "packages": [
            {
                "name": "Sacred Kashi, Prayagraj & Ayodhya Yatra",
                "destination": "Uttar Pradesh",
                "duration": "4 Nights / 5 Days",
                "starting_price_inr": 29500,
                "highlights": "Kashi Vishwanath VIP Darshan, private boat for Ganga Aarti, Triveni Sangam Snan, Ayodhya Ram Mandir Darshan.",
                "category": "Spiritual Teerth"
            },
            {
                "name": "Char Dham Yatra by Luxury Bus / Heli",
                "destination": "Yamunotri, Gangotri, Kedarnath, Badrinath",
                "duration": "9 Nights / 10 Days",
                "starting_price_inr": 58000,
                "highlights": "Haridwar to Haridwar, Kedarnath helicopter tickets assistance, puja samagri, medical assistance team.",
                "category": "Sacred Pilgrimage"
            }
        ]
    },
    {
        "id": "tenant_devlancer",
        "slug": "devlancer",
        "assistant_id": "asst_devlancer",
        "name": "devlancer",
        "category": "tech_saas",
        "tagline": "Autonomous AI Workflows, Chatbots & Custom Software Systems",
        "website_url": "https://quick-silver-yrqlyyf.vercel.app",
        "logo_url": "https://www.google.com/s2/favicons?domain=quick-silver-yrqlyyf.vercel.app&sz=128",
        "primary_color": "#ffffff",
        "secondary_color": "#2b2b2b",
        "accent_color": "#ff9900",
        "assistant_name": "devlancer",
        "welcome_message": "welcome to devlancer , how may i help you !",
        "personality_prompt": "You are 'devlancer AI', the intelligent digital concierge for devlancer. We architect, engineer, and deploy intelligent software systems that eliminate operational bottlenecks and scale without human friction. We provide Autonomous AI workflows, chatbots, and custom software, websites, etc.",
        "knowledge_base": "we provide Autonomous AI workflows, chatbots , and custom software , websites etc.... We architect, engineer, and deploy intelligent software systems that eliminate operational bottlenecks and scale without human friction.",
        "supported_languages": "English, Hindi",
        "contact_phone": "6006213273",
        "contact_email": "",
        "contact_address": "",
        "webhook_url": "https://docs.google.com/spreadsheets/d/1Hk7YtYjv-ILd3GynpL-xIUTqtmJD2xPyPQtUSgpIUG8/edit?gid",
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": "standard",
        "tone_of_voice": "Professional, warm, and expert travel consultant",
        "store_chat_history": 1,
        "packages": []
    },
    {
        "id": "tenant_cricbuzz_com",
        "slug": "cricbuzz-com",
        "assistant_id": "asst_cricbuzz_com",
        "name": "Cricbuzz",
        "category": "sports_cricket",
        "tagline": "Live Cricket Scores, News, Stats and Fixtures",
        "website_url": "https://cricbuzz.com",
        "logo_url": "https://www.google.com/s2/favicons?domain=cricbuzz.com&sz=128",
        "primary_color": "#009270",
        "secondary_color": "#03634c",
        "accent_color": "#f59e0b",
        "assistant_name": "CricBot",
        "welcome_message": "Welcome to Cricbuzz! How can I help you follow the game today? 🏏",
        "personality_prompt": "You are CricBot, the official cricket concierge for Cricbuzz. Provide live ball-by-ball commentary, player stats, team rankings, match schedules, tournament news, and cricket analysis.",
        "knowledge_base": "Cricbuzz is the premier destination for live cricket coverage, offering ball-by-ball commentary, live scores, player statistics, rankings, schedule of upcoming matches, and in-depth news and analysis from the world of cricket.",
        "supported_languages": "English, Hindi, International",
        "contact_phone": "",
        "contact_email": "",
        "contact_address": "",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": "standard",
        "tone_of_voice": "High-Energy Sports",
        "store_chat_history": 0,
        "packages": []
    },
    {
        "id": "tenant_1794458762071",
        "slug": "movie-rating",
        "assistant_id": "asst_movie_rating",
        "name": "imdb",
        "category": "entertainment_movies",
        "tagline": "Ratings, Reviews, and Where to Watch the Best Movies & TV Shows",
        "website_url": "https://www.imdb.com/",
        "logo_url": "https://www.google.com/s2/favicons?domain=imdb.com&sz=128",
        "primary_color": "#f5c518",
        "secondary_color": "#121212",
        "accent_color": "#f5c518",
        "assistant_name": "IMDb Concierge",
        "welcome_message": "Welcome to IMDb! Discover top-rated movies, cast details, ratings, and recommendations. How can I help you today? 🎬",
        "personality_prompt": "You are IMDb Concierge. The authoritative expert on movie rankings, box office hits, cast details, trivia, and reviews.",
        "knowledge_base": "IMDb is the authoritative source for movie ratings, reviews, top 250 lists, cast, directors, release dates, and awards. Top movies include The Shawshank Redemption (9.3), The Godfather (9.2), The Dark Knight (9.0), 12 Angry Men (9.0), Schindlers List (9.0).",
        "supported_languages": "English, Hindi",
        "contact_phone": "",
        "contact_email": "",
        "contact_address": "",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": "standard",
        "tone_of_voice": "Cinephile Critic",
        "store_chat_history": 0,
        "packages": []
    },
    {
        "id": "tenant_1794459683314",
        "slug": "products---e-comerce",
        "assistant_id": "asst_products___e_comerce",
        "name": "amazon",
        "category": "ecommerce",
        "tagline": "Online Shopping for Electronics, Apparel, Books & More",
        "website_url": "https://www.amazon.com/",
        "logo_url": "https://www.google.com/s2/favicons?domain=amazon.com&sz=128",
        "primary_color": "#ff9900",
        "secondary_color": "#131921",
        "accent_color": "#ff9900",
        "assistant_name": "Amazon Concierge",
        "welcome_message": "welcome to Amazon! Find products, check customer reviews, track orders, and compare prices.",
        "personality_prompt": "You are Amazon Concierge. Help customers find products, compare specs, check reviews and shipping.",
        "knowledge_base": "Amazon e-commerce platform catalog, products, reviews, deals and customer assistance.",
        "supported_languages": "English, Hindi",
        "contact_phone": "",
        "contact_email": "",
        "contact_address": "",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": "standard",
        "tone_of_voice": "Helpful, knowledgeable, and customer-obsessed",
        "store_chat_history": 0,
        "packages": []
    },
    {
        "id": "tenant_nike_com",
        "slug": "nike-com",
        "assistant_id": "asst_nike_com",
        "name": "Nike",
        "category": "ecommerce",
        "tagline": "Just Do It. Premium Athletic Footwear & Apparel",
        "website_url": "https://nike.com",
        "logo_url": "https://www.google.com/s2/favicons?domain=nike.com&sz=128",
        "primary_color": "#111111",
        "secondary_color": "#000000",
        "accent_color": "#fa541c",
        "assistant_name": "Nike Assistant",
        "welcome_message": "Welcome to Nike! How can I help you find your next pair of kicks or gear today?",
        "personality_prompt": "You are Nike Digital Assistant. Inspiring, energetic, athletic, and knowledgeable about Nike sportswear, Pegasus running shoes, Jordan sneakers, Air Force 1s, and athletic sizing.",
        "knowledge_base": "Nike athletic shoes, running sneakers, lifestyle apparel, athletic innovations, and size guidance.",
        "supported_languages": "English, Hindi",
        "contact_phone": "",
        "contact_email": "",
        "contact_address": "",
        "webhook_url": "",
        "allowed_domains": "*",
        "is_active": 1,
        "default_detail_level": "standard",
        "tone_of_voice": "Energetic, inspiring, and athletic",
        "store_chat_history": 0,
        "packages": []
    }
]

def seed_database(default_webhook_url: str = ""):
    """Seeds default tenants and packages into the database if not already present."""
    init_db()
    with get_connection() as conn:
        print("[DB SEED] Checking Devlancer multi-tenant travel agencies...")
        existing_slugs = {r[0] for r in conn.execute("SELECT slug FROM tenants;").fetchall()}
        
        seeded_count = 0
        for raw_t in SEED_TENANTS:
            t_data = dict(raw_t)
            packages = t_data.pop("packages", [])
            # If slug not present, seed it!
            if t_data["slug"] not in existing_slugs:
                if t_data["id"] == "tenant_prakruthi" and default_webhook_url:
                    t_data["webhook_url"] = default_webhook_url
                upsert_tenant(t_data)
                set_tenant_packages(t_data["id"], packages)
                seeded_count += 1
            else:
                # Update webhook if available
                if t_data["id"] == "tenant_prakruthi" and default_webhook_url:
                    conn.execute("UPDATE tenants SET webhook_url = ? WHERE id = 'tenant_prakruthi' AND (webhook_url = '' OR webhook_url IS NULL);", (default_webhook_url,))
                    conn.commit()
                    
        if seeded_count > 0:
            print(f"[DB SEED] Successfully seeded {seeded_count} new tenants with packages!")
        else:
            print(f"[DB SEED] All {len(existing_slugs)} tenants already present in database.")
