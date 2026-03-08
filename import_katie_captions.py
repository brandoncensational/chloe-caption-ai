"""
import_katie_captions.py
Imports Katie Riedel's used captions from all readable monthly batch files.

Sources read directly from Google Drive:
  ✅ February 2026  — 10 posts (full)
  ✅ January 2026   —  2 posts (partial — file was truncated in Drive API)
  ✅ November 2025  — 12 posts (full)
  ✅ October 2025   — 12 posts (full)
  ✅ September 2025 — 12 posts (full)
  ❌ August 2025    — file too large for Drive API
  ❌ July 2025      — file too large for Drive API
  ❌ December 2025  — no batch doc found in folder
  ❌ March 2026     — folder just created, no doc yet

Total: 48 real captions imported
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, get_clients, add_example

CAPTIONS = [

    # ═══ FEBRUARY 2026 (10 posts) ══════════════════════════════════════════

    ("Adventure + Chill in Your Tipi – TOTG Reel – Feb 2026",
     "Spring Break looks different out here. Mornings start with coffee and river mist instead of alarms. Days unfold however you want them to. Paddle or sit riverside for hours. Float with nowhere to be. Settle into your Tipi and let the world slow down.\n\nIf you have been craving space to breathe and room to play, your glamping adventure at the Tipis is waiting. 🏕️💛\n#GlampingVibes #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #SpringBreakEscape #TXHillCountry #RiverLife #AdventureAndChill #GlampingTexas"),

    ("Spring Break, Riverside Style – TOTG Carousel – Feb 2026",
     "This is Spring Break without the noise. Just you, the river, and days that move at your pace. Wander our trail or float on the water. Take a nap under the trees and wake up to sunlight dancing on the river. Rent a kayak and see where the river takes you.\n\nOnce you get into the rhythm of our Tipi resort, it's hard to imagine being anywhere else. ✨\n#GlampingVibes #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #SpringBreakAdventure #RiverLife #TXHillCountry #GlampingTexas #tipiresort #kayaktexas #riverfishing"),

    ("Riverside Romance Just for Two this Valentine's Day – CWR Reel – Feb 2026",
     "Valentine's Day feels right at our retreat cabins. Quiet mornings wrapped in blankets. Gentle paddles on calm rivers. Evenings lit by firelight and conversation that does not need rushing.\n\nThis is the kind of place where you actually hear each other again. If that sounds like your idea of romance, this is your sign to book it. 💛\n#RiversideRomance #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #CouplesRetreat #GlampingTexas #GoodVibesOnly #booknow"),

    ("Love in the Hill Country on Valentine's Day – CWR Carousel – Feb 2026",
     "Our retreat cabins are designed for unhurried moments. Cabins glowing after sunset. Cozy spaces that invite you to linger. River views that do most of the talking.\n\nWhether you are planning a Valentine's surprise or simply carving out much-needed time together, this is where memories settle in and stay. 💌\n#RomanceEscape #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #CouplesGetaway #RiversideMagic #GlampingTexas"),

    ("Spring Break, Reel Style – RRE Reel – Feb 2026",
     "Morning mist, a rod in your hand, and the thrill of the first catch. Afternoon naps by the river, evening campfires, and laughter echoing over the water… River Road Escapes is your Spring Break escape for all of it. 🌊\nBook your cabin and make your fishing stories legendary.\n#FishingTrip #RiverRoadEscapes #TipisOnTheGuadalupe #CalmWaterRentals #TXHillCountry #RiverLife #GlampingTexas #SpringBreakFishing #AdventureByTheRiver"),

    ("Riverside Fun + Fishing Adventures – RRE Carousel – Feb 2026",
     "Sunrise casts, afternoon giggles, and campfires that last past bedtime. River Road Escapes gives you the full riverside experience. 🎣\nWhether it's your first fishing trip or your tenth, you'll leave with more than fish, you'll have memories that stick. We can also recommend a fishing guide for an unforgettable experience!\n\nSpots are filling fast– don't miss out!\n#FishingTrip #RiverRoadEscapes #TipisOnTheGuadalupe #CalmWaterRentals #TXHillCountry #RiverLife #GlampingTexas #SpringBreakAdventure"),

    ("Last Spring Break Memories and What's Coming Next – Katie Static – Feb 2026",
     "Last Spring Break still makes me smile. Floating the river with a drink in hand. Sun on my face. Not checking the time once. Those simple moments are the reason I love this place so much.\n\nWith another season right around the corner, I cannot wait to watch new stories unfold on the river. Spring is almost here and it always brings something special. Book with us today! 💛\n#SpringBreak #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #RiverLife #GlampingTexas"),

    ("A Little Valentine's Day Joy – Katie Reel – Feb 2026",
     "Right before Valentine's Day, this feels like the reminder we all need. Love does not have to be loud or overplanned to be meaningful. Sometimes it is laughing, dancing and soaking up the joy right in front of you.\n\nWhether you are celebrating with someone you love or simply celebrating being alive here and now, I hope your tomorrow feels full in the best way. 💛\n#ValentinesDay #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #GlampingTexas #RiverLife #WomenOwnedBusiness"),

    ("Guest Stories: Why They Keep Coming Back – Katie Reel – Feb 2026",
     "I hear this more often than anything else, and it never feels routine. Seeing people connect with this place, slow down, and genuinely enjoy their time here is why I care so deeply about what we've built. Our 5-Star track record speaks for itself.\n\nIf Spring Break on the river has been calling your name, I would love to help you plan a stay that feels just as hard to leave! 💛\n#GuestLove #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #GlampingTexas #RiverLife"),

    ("Katie's Morning Reflection – Katie Static – Feb 2026",
     "This is one of those spots I always hope people take a moment to really enjoy. Warm sunlight through the trees, a quiet place to sit, and the feeling that you are tucked away in nature even though the river is just beyond view.\n\nI love creating spaces like this, where slowing down feels natural and time is not asking anything from you. These are the moments guests tell me they remember most. 🌿\n#MorningMagic #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #TXHillCountry #WomenOwnedBusiness #RiverLife #GlampingTexas #GoodVibes"),

    # ═══ JANUARY 2026 (2 posts — file was truncated) ══════════════════════

    ("Air, Water, Earth – RRE Reel – Jan 2026",
     "From sunrise drives to star-filled nights, River Road has its own kind of magic.\nIt's the place you come to breathe, rest, and recharge.\nPlan your next Hill Country trip directly through the link in our bio. ✨\n#RiverRoadMagic #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas"),

    ("Your Winter Reset Awaits – CWR Carousel – Jan 2026",
     "If you have been craving a reset, a winter river stay is the perfect way to slow down before the new year.\nSoft mornings, quiet afternoons and nights that feel intentionally cozy.\nReady to experience the magic for yourself? Whether it is a peaceful getaway or an adventure filled weekend, we have the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape.\n#WinterReset #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas"),

    # ═══ NOVEMBER 2025 (12 posts) ══════════════════════════════════════════

    ("Cabin Tour – La Pluma – Carousel – Nov 2025",
     "Peaceful mornings, cozy corners, and the river just beyond your door. 🛶\nEvery couple's stay here is made for comfort, connection, and a little bit of adventure.\nReady when you are — book your next getaway through our link in bio. ✨\n#HillCountryCabinTour #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #Romantic #CouplesGetaway"),

    ("Good Vibes Destination – CWR Carousel – Nov 2025",
     "Good vibes, great views, and that feeling you only get by the water.\nWhether you're here to unwind or fill your days with river time and sunshine, this stretch of the Guadalupe never disappoints.\n#GoodVibesGetaway #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Happy Halloween / Spooky Tipis – Static – Nov 2025",
     "Spooky season hits a little different at the Tipis. 🎃\n\nCool nights, crackling campfires, and the Guadalupe River rippling and glowing under the moon — it's pure magic out here this time of year.\n\nHappy Halloween from our little corner of the Guadalupe. ✨\n#SpookySeasonAtTheTipis #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("AirHaus Airbnb Tour – RRE Reel – Nov 2025",
     "A guest favorite for good reason. The Air Haus blends rustic charm with modern comfort in the best way.\nPerfect for couples, small families, or anyone who just needs a little peace and quiet (you can also rent the full house for up to 18 guests!).\nBook your fall stay now! 🍁\n#AirHausStay #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Cabin/Tipi Activities – Reel – Nov 2025",
     "Every stay comes with its own mix of adventure and chill.\nThrow a basketball, hit the ping pong table, float down the river, cozy up by the firepit, or unwind with a glass of wine as the sun sets.\nOur properties are all about making memories, one fun moment at a time. ✨\n\nPlan your next getaway with Calm Water Rentals and see what adventures await — link in bio!\n#TipisWeekendVibes #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Cozy Colorful Spaces – Reel – Nov 2025",
     "Every space here has its own personality: bright, cozy, and full of charm.\n\nThe colors in our properties make you smile the second you walk in, and the textures just make you want to sink in and stay awhile.\n\nIt's warm, welcoming, and a little bit playful: exactly how a getaway should feel. 💚\n\nReady to see these spaces for yourself? Book your stay through the link in our bio and come get cozy. ✨\n#CozyColorfulStay #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Story Behind the Tipis – Carousel – Nov 2025",
     "Every stay has a story… and so do the Tipis. ✨\n\nThis all started with a simple dream: to create a place where people could slow down, breathe a little deeper, and remember what it feels like to be surrounded by nature.\n\nThe Tipis were built to be unique, rustic, and peaceful — a reminder that comfort doesn't have to mean complicated. They've become more than just a stay… they're part of so many people's stories now, and that's the best part of all. 💚\n#StoryOfTheTipis #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Guadalupe River Moments – CWR Reel – Nov 2025",
     "There's something about Fall at the Guadalupe that just resets your soul.\n\nThe sound of the water, the way the light dances on the surface, the calm that settles in without you even realizing it.\n\nThis is where everything slows down, and somehow, everything starts to feel right again.\n\nPlan your Fall river escape today — your peaceful reset is waiting. 🍁\n#GuadalupeRiverDays #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Getting Ready for the Cold – RRE Carousel – Nov 2025",
     "Sweater weather and cabin views — the perfect pair. 🍂\n\nThere's something about this time of year that slows everything down. The air feels quieter, the river moves a little softer, and nights by the campfire last just a little longer.\n\nWe've got the firewood stacked, the blankets waiting, and the coziest spaces ready for your next getaway.\n\nBook your fall or winter stay through the link in our bio and come experience a glamping adventure for yourself. ✨\n#CozyCabinSeason #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("Night Shots of the Cabins / Tipis – Carousel – Nov 2025",
     "When the sun goes down, the glow begins. ✨\n\nThere's a kind of peace that settles over the Tipis at night — the hum of the day fades, folks fire up their BBQ pits, fires start to crackle, and a general happiness falls over the entire campground.\n\nIt's the moment that reminds you how simple and beautiful life can be when you slow down enough to notice it. 🌙\n#NightsAtTheTipis #FirepitNights #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #CampgroundFun"),

    ("Spending Time With Friends, Families, and Loved Ones – Reel – Nov 2025",
     "The best part of a river getaway isn't the view; it's the moments shared in between. 🌿\n\nThe unplanned laughter, the long talks that stretch into the night, the quiet comfort of just being together.\n\nHere, life feels simple again. No rush, no noise, just connection; the kind that stays with you long after the trip ends.\n\nBring your people, make it yours, and let the river do the rest. ✨\n#GatherByTheRiver #CalmWaterMoments #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    ("CWR Experience – Carousel – Nov 2025",
     "Peaceful stays, easy planning, and memories that linger long after you leave — that's what staying at the Tipis on the Guadalupe is really about.\n\nWe take care of the little details so you can do what matters most: slow down, breathe in the river air, watch the sunlight on the water, and truly be present with the people you came with. 🌿\n\nReady to plan your next river getaway? Book your stay through the link in our bio. ✨\n#CalmWaterExperience #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes"),

    # ═══ OCTOBER 2025 (12 posts) ══════════════════════════════════════════

    ("Cozy Evening at the Tipis – Static – Oct 2025",
     "Cool FALL evenings & pink skies = 😍🍂😍🍁😍🍂\n\nThat's the kind of magic waiting when you wake up at the Tipis.\n\nTake it slow, sip your coffee outside, and let FALL in the Hill Country do the rest. 🍁🍂\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your FALL escape!\n#FallGlampingTexas #TexasGlampingEscape #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Fall at the River Just Makes Sense – Reel – Oct 2025",
     "Here's what Fall at the river looks like:\n\n🌊 Crisp air by the water\n🔥 Firepit glow\n✨ Starry skies after dark\n\nRiverfront glamping season = officially here. Who's in? 🏕️🙋🏼‍♀️\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacations #Autumn #ComalRiver #GuadalupeRiver"),

    ("Why It's So Easy to Book Now – Website Carousel – Oct 2025",
     "We redesigned our website for YOU ✨. Here's why it's easier than ever to plan your getaway:\n\n✅ Simple, mobile-friendly booking\n✅ Clear property photos + details\n✅ Quick confirmation emails\n\nNo fuss, just one click to cozy. Book now at tipisontheguad.com (link in bio)! 💻\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays #BookNow"),

    ("Kayak Promo Moment – CWR Reel – Oct 2025",
     "The best part of a Hill Country stay? The river is right here.\n\n✔️ Onsite kayak rentals\n✔️ Same-day self-serve launch\n✔️ Perfect for pairing with your Tipi or Cabin getaway\n\nYour river adventure = waiting for you. 🌊\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays #booknow #glamping"),

    ("What to Pack for a Cozy River Getaway – Carousel – Oct 2025",
     "Not sure what to pack for your Hill Country escape? We've got you:\n\n🧥 A cozy sweater for fall mornings\n👟 Comfy shoes for river road walks\n🎲 Games or a book for downtime\n🔥 S'mores ingredients! (We sell firewood and s'mores on site!)\n\nKeep it simple—nature does the rest. 🍂\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Guest Spotlight – Malinda's Review – Static – Oct 2025",
     "\"The kids and I just got back from this paradise! Absolutely gorgeous! So quiet and peaceful! There was an abundance of wildlife and the river was breathtaking! The sounds of friends and families having a blast echo up the clear river! This will be our special spot from now on! Say hi to the black kitty when you visit!\" – Malinda 💚\n\nBig thank you to Malinda for sharing this sweet review with us; we're so glad your family had such a wonderful stay! ✨\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("River Road Escapes Cabin Vibes – RRE Carousel – Oct 2025",
     "Your RRE cabin = the perfect fall retreat. 🍂\n\nSpacious kitchens, cozy couches, bright bathrooms, and everything else you need to have an amazing experience.\n\nBecause a cabin by the river isn't just a stay—it's a memory in the making. 💙\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("River Road in October – Reel – Oct 2025",
     "Scenic drives, cool breezes, and the Guadalupe flowing by your side — fall in the Hill Country is hard to beat. 🍁🌊\n\nPlan your Fall escape now for a weekend getaway NOW!\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your Autumn escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #AutumnEscape #NewBraunfelsTX #ExploreTexas #NatureStays #flyfishing"),

    ("Local Spotlight: Fall Fun in New Braunfels – Carousel – Oct 2025",
     "October = small town fun with big charm. Here's what's on our list:\n\n🎃 Fall markets + pumpkin patches\n🍺 Local breweries + beer gardens\n🍂 Scenic hikes + drives\n\nMake your getaway even better with a little local exploring!\n\nReady to experience the magic for yourself? Whether it's a peaceful getaway or an adventure-filled weekend, we've got the perfect spot waiting for you. Send us a DM or hit the link in our bio to start planning your escape!\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Tipi Night Tour – Firepit + Lights Reel – Oct 2025",
     "When the sun sets, the Tipis light up.\n\nCozy fires, string lights, and the sounds of the river = Fall perfection.\n\nBook your stay now—link in bio. ✨\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("RRE Cabin Montage – Reel – Oct 2025",
     "Your stay at River Road Escapes is more than just a cabin in the woods — it's a collection of little moments you'll always remember 💚\n\nMorning coffee in the kitchen, slow porch sits with a view, grilling up dinner outside, sinking into the couch after a day on the water, and tucking into comfy beds at night. Every detail is designed to make you feel at home while still giving you that special getaway feeling.\n\nReady to start making your own memories? Book now through the link in bio. ✨\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Aerial View of the Tipis – Reel – Oct 2025",
     "From above, you can see just how perfectly tucked away these Tipis really are. 🌿\n\nSurrounded by Hill Country beauty, steps from the river, and still just a short drive to restaurants, shops, and local attractions. It's the kind of place where you can spend the day exploring, then come home to peace and quiet — with comfy couches, modern kitchens, and a river deck made for sunset watching.\n\nEscape the noise, soak in the views, and recharge riverside. Book your stay today through the link in bio. ✨\n#WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #FallVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    # ═══ SEPTEMBER 2025 (12 posts) ═════════════════════════════════════════

    ("Labor Day – Static – Sep 2025",
     "To the workers, dreamers, and doers– today we celebrate you. 🙌\n\nLabor Day is about honoring the effort it takes to keep things moving, from job sites and classrooms to hospitals, homes, and everywhere in between.\n\nHere at the river, we believe hard work deserves its reward: a quiet moment under the trees, toes splashing the water, laughter by the fire, and memories with the people who matter most. ✨\n\nWishing you a safe and restful Labor Day from all of us at Tipis on the Guadalupe. 💙\n#LaborDay #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Little Things That Just Make Sense at the Tipis – Reel – Sep 2025",
     "You know those small-but-mighty details that make a getaway feel effortless? Here's what guests say just makes sense at the Tipis:\n\n☕ Coffee station for slow mornings\n🪑 Outdoor seating under twinkling lights\n🎲 Games & lawn space for family fun\n🔥 Firepit vibes at night\n\nNature + comfort = the perfect match.\n#TipiStay #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("How to Book in 3 Steps – Website Carousel – Sep 2025",
     "Booking your Hill Country escape has never been easier (and we're obsessed with our new site ✨).\n\nHere's how to lock in your stay in 3 quick steps:\n\n1️⃣ Visit tipisontheguad.com\n2️⃣ Choose your dates + property\n3️⃣ Book instantly! 💻\n\nThen get ready to \"GLAMP\" the night away! Your cozy Tipi cabin or riverfront rental is literally a click away. Ready to get started? 👇 Link in bio.\n#BookNow #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Meet Your Kayak Rentals – CWR Reel – Sep 2025",
     "No need to haul gear – your kayak rental is ready onsite. At Calm Water Rentals, you can:\n\n✔️ Rent kayaks right by the water\n✔️ Pair with your stay at Tipis or River Road Escapes\n✔️ Launch + paddle the Guadalupe same day - it's self-serve and we make it easy!\n\nThe only thing missing? You.\n#KayakRentals #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Best Fall Activities Around New Braunfels – Carousel – Sep 2025",
     "September = prime Hill Country season. 🍂\n\nHere's what we love:\n\n🍺 Wurstfest in downtown NB - coming in November!\n🎶 Gruene Hall concerts all month\n🍎 Apple picking + farm stands nearby\n🚗 Scenic drives on River Road\n🌌 Crisp nights under starry skies\n\nBook your Fall Glamping Experience now before weekends fill up! Link in bio.\n#FallActivities #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Guest Spotlight – Courtney's Review – Reel – Sep 2025",
     "Sometimes the best adventures are the ones you don't plan. ✨\n\n\"My family and I just got in the car, picked a direction, and drove! We found this little gem on the way, and even late at night the host was very responsive. Our kiddos loved sleeping in a Tipi! It's a quiet place and not far from restaurants and tourist attractions. We will be planning another trip!\" – Courtney\n\nWe're so glad you and your family enjoyed your stay, Courtney, and we can't wait to welcome you back for the next adventure! ⛺️🌿\n\nWe're all about making your stay easy, cozy, and unforgettable. Ready to create your own memory? Link in bio!\n#GuestSpotlight #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Tour a Tipi in 15 Seconds – Reel – Sep 2025",
     "What does it actually look like inside a Tipi? Cozy beds, A/C, thoughtful details, and rustic charm all rolled into one. Book a stay and see it for yourself. Link in bio!\n#TipiTour #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("River Day Moments – CWR + RRE Reel – Sep 2025",
     "Your River Road weekend should look a little like this:\n\n🛶 Paddles in the water\n🎣 Lines cast at sunset\n🔥 Campfire laughter at night\n\nThat's river life, and it's waiting for you. 💫\n#RiverDays #RiverMoments #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("What's Included in My Cabin Stay? – RRE Carousel – Sep 2025",
     "Your tiny river cabin = more than just a roof over your head. Every stay includes:\n\n🛏️ Comfy beds + linens\n☕ Coffee and outdoor spaces to start the day right\n🛁 Bright, clean bathrooms to refresh and recharge\n🍳 Spacious kitchens for cooking and gathering\n🔥 Outdoor grills for easy meals together\n🛋️ Cozy couches + amenities to unwind\n\nBook now and make it yours– link in bio!\n#CabinStay #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Why Book Direct? – Promo Carousel – Sep 2025",
     "PSA: Booking direct = best perks. 🙌\n\nWhen you book through our website:\n\n✅ Save 10% with code STAYCALM\n✅ Get return guest discounts\n✅ Access last-minute promos\n✅ Enjoy easier communication & faster booking\n\nDon't miss out– link in bio to plan your stay today.\n#BookingDirect #Promos #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Team Spotlight – Sonia the Housekeeping Hero – Static – Sep 2025",
     "Meet the woman who makes your getaway shine ✨🧺\n\nOur Property Manager & Housekeeper, Sonia, is the heart of the operation– making sure every bed is fresh, every cabin is sparkling, and every stay feels like home.\n\nDrop her some love in the comments! 👏\n#TeamSpotlight #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),

    ("Local Spotlight – River Road Foodie Stops – Carousel – Sep 2025",
     "River days = hungry crews. Here's where we send guests:\n\n🍔 Jay & Diane's Horseshoe Grill\n🌮 Tacos Don Chente\n🍦 Scoops & Roots\n☕ Sweetie's Bakery\n\nTag your go-to River Road food stop– we're always looking for more favorites!\n#NewBraunfelsEats #WomenOwnedBusiness #TipisOnTheGuadalupe #CalmWaterRentals #RiverRoadEscapes #GoodVibes #CanyonLake #VisitNewBraunfels #TexasHillCountryGetaway #RiverLife #GlampingTexas #KayakTexas #SummerVacayVibes #NewBraunfelsTX #ExploreTexas #NatureStays"),
]


def find_katie_client():
    clients = get_clients()
    for c in clients:
        if any(k in c["name"].lower() for k in ["katie", "calm water", "calmwater", "tipi", "riedel"]):
            return c
    return None


def run_import():
    init_db()
    print("\n╔══════════════════════════════════════════════════╗")
    print("║   Katie Riedel — Caption Import                  ║")
    print("║   Sep / Oct / Nov 2025 + Jan / Feb 2026          ║")
    print("║   48 real captions from Google Drive             ║")
    print("╚══════════════════════════════════════════════════╝\n")

    client = find_katie_client()
    if not client:
        clients = get_clients()
        print("Could not auto-detect Katie's client. Available clients:")
        for i, c in enumerate(clients):
            print(f"  {i+1}. {c['name']} (ID: {c['id']})")
        if not clients:
            print("\n  No clients yet. Add Katie's client in the app first.\n")
            return
        choice = input("\nEnter the number of Katie's client: ").strip()
        try:
            client = clients[int(choice) - 1]
        except (ValueError, IndexError):
            print("Invalid. Exiting.")
            return

    print(f"Client: {client['name']} (ID: {client['id']})")
    print(f"Importing {len(CAPTIONS)} captions as 'used' examples...\n")

    imported = skipped = 0
    for context, caption in CAPTIONS:
        try:
            add_example(client_id=client["id"], caption=caption, label="used",
                        context=context, platform="Instagram/TikTok", engagement="")
            print(f"  ✅  {context[:65]}")
            imported += 1
        except Exception as e:
            print(f"  ⚠️  Skip: {context[:50]} — {e}")
            skipped += 1

    print(f"\n{'─'*55}")
    print(f"  Done!  ✅ {imported} imported   ⚠️  {skipped} skipped")
    print(f"  The AI now has {imported} real Calm Water captions as")
    print(f"  style references for this client.")
    print(f"{'─'*55}\n")


if __name__ == "__main__":
    run_import()
