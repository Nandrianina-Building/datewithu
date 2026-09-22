"""
Peuple la base avec des données réelles et complètes sur Madagascar :
villes, catégories, lieux, ambiances, budgets, occasions, activités et
packages « clé en main ».

Toutes les villes, tous les lieux et tous les points d'intérêt utilisés
ici sont réels (quartiers, adresses approximatives, coordonnées GPS) —
recherchés spécifiquement pour Date With U plutôt que générés au hasard,
afin que l'application ait un contenu crédible dès l'installation.

Idempotent : basé sur `update_or_create`, on peut le relancer sans
créer de doublons (utile après un `git pull` qui ajoute nommage/lieux).

Usage :
    python manage.py seed_madagascar
    python manage.py seed_madagascar --flush   # vide les tables avant de reseeder
"""

import mimetypes

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.activities.models import Activity
from apps.budgets.models import Budget
from apps.catalog.models import Category, Place
from apps.core.models import SiteConfiguration
from apps.locations.models import City
from apps.moods.models import Mood
from apps.occasions.models import Occasion
from apps.packages.models import DatePackage


class Command(BaseCommand):
    help = "Peuple la base avec des données complètes et réelles sur Madagascar (villes, lieux, activités, packages...)."
    commons_api = "https://commons.wikimedia.org/w/api.php"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush", action="store_true",
            help="Supprime d'abord tout le contenu catalogue existant (villes, lieux, activités, packages, ambiances, budgets, occasions, catégories).",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Suppression du contenu catalogue existant...")
            DatePackage.objects.all().delete()
            Activity.objects.all().delete()
            Place.objects.all().delete()
            Category.objects.all().delete()
            City.objects.all().delete()
            Mood.objects.all().delete()
            Budget.objects.all().delete()
            Occasion.objects.all().delete()

        with transaction.atomic():
            cities = self._seed_cities()
            categories = self._seed_categories()
            places = self._seed_places(cities, categories)
            moods = self._seed_moods()
            budgets = self._seed_budgets()
            self._seed_occasions()
            activities = self._seed_activities(cities, places, categories, moods, budgets)
            self._seed_packages(cities, places, activities, moods, budgets)
            self._seed_site_config()
            self._seed_blog(cities)
            self._seed_premium_plans()

        self.stdout.write(self.style.SUCCESS(
            f"Terminé : {City.objects.count()} villes, {Category.objects.count()} catégories, "
            f"{Place.objects.count()} lieux, {Mood.objects.count()} ambiances, "
            f"{Budget.objects.count()} budgets, {Occasion.objects.count()} occasions, "
            f"{Activity.objects.count()} activités, {DatePackage.objects.count()} packages."
        ))

    def _download_real_image(self, instance, field_name, search_name, folder):
        """Fetch one relevant Wikimedia Commons image and store it locally."""
        if getattr(instance, field_name):
            return

        try:
            response = requests.get(
                self.commons_api,
                params={
                    "action": "query", "format": "json", "generator": "search",
                    "gsrsearch": f"{search_name} Madagascar",
                    "gsrnamespace": 6, "gsrlimit": 1,
                    "prop": "imageinfo", "iiprop": "url|mime", "iiurlwidth": 900,
                },
                headers={"User-Agent": "DateWithU seed importer/1.0"},
                timeout=20,
            )
            response.raise_for_status()
            pages = response.json().get("query", {}).get("pages", {})
            page = next(iter(pages.values()), None)
            image_info = (page or {}).get("imageinfo", [{}])[0]
            image_url = image_info.get("thumburl") or image_info.get("url")
            if not image_url or not image_info.get("mime", "").startswith("image/"):
                return

            image = requests.get(
                image_url,
                headers={"User-Agent": "DateWithU seed importer/1.0"},
                timeout=30,
            )
            image.raise_for_status()
            extension = mimetypes.guess_extension(image_info.get("mime", "")) or ".jpg"
            filename = f"{slugify(search_name)[:90]}{extension}"
            getattr(instance, field_name).save(
                f"{folder}/{filename}", ContentFile(image.content), save=False,
            )
            instance.save(update_fields=[field_name])
        except (requests.RequestException, ValueError, StopIteration) as error:
            self.stderr.write(f"Image ignorée pour {search_name}: {error}")

    # ------------------------------------------------------------------
    # Villes
    # ------------------------------------------------------------------

    def _seed_cities(self):
        self.stdout.write("Villes...")
        # (nom, région, description, latitude, longitude, ordre)
        data = [
            ("Antananarivo", "Analamanga",
             "La capitale malgache, perchée sur ses douze collines sacrées. Entre marchés animés, "
             "restaurants gastronomiques et panoramas sur la Haute-Ville, « Tana » concentre l'essentiel "
             "de la vie culturelle et nocturne du pays.",
             -18.8792, 47.5079, 0),
            ("Toamasina", "Atsinanana",
             "Tamatave pour les intimes : le principal port du pays, ses plages en bord de ville et le "
             "Canal des Pangalanes juste à côté pour une balade en pirogue romantique.",
             -18.1492, 49.4023, 1),
            ("Antsirabe", "Vakinankaratra",
             "La ville thermale des Hauts Plateaux, célèbre pour ses pousse-pousse colorés, son air frais "
             "et ses lacs de cratère (Andraikiba, Tritriva) parfaits pour une échappée en amoureux.",
             -19.8659, 47.0333, 2),
            ("Mahajanga", "Boeny",
             "Majunga pour les habitués : une ville côtière au bord du canal du Mozambique, connue pour "
             "son baobab centenaire sur le front de mer et ses couchers de soleil.",
             -15.7167, 46.3167, 3),
            ("Fianarantsoa", "Haute Matsiatra",
             "La capitale du Betsileo et de la vigne malgache : vieille ville coloniale escarpée, "
             "cathédrale et domaines viticoles à visiter à deux.",
             -21.4536, 47.0854, 4),
            ("Toliara", "Atsimo-Andrefana",
             "Tuléar pour les anciens : porte d'entrée du sud aride et de ses plages de sable blanc, à "
             "deux pas des récifs coralliens d'Ifaty.",
             -23.3516, 43.6709, 5),
            ("Antsiranana", "Diana",
             "Diego-Suarez pour les habitués : une baie spectaculaire, la Mer d'Émeraude et les Tsingy "
             "Rouges à quelques kilomètres — un décor rêvé pour les couples aventuriers.",
             -12.2787, 49.2917, 6),
            ("Nosy Be", "Diana",
             "L'« île aux parfums », première destination balnéaire du pays : plages de sable blanc, "
             "ylang-ylang et couchers de soleil sur le canal du Mozambique.",
             -13.3167, 48.2667, 7),
            ("Morondava", "Menabe",
             "La ville portes d'entrée de la mythique Allée des Baobabs — l'un des couchers de soleil "
             "les plus romantiques du monde.",
             -20.2833, 44.3167, 8),
            ("Sambava", "Sava",
             "Capitale malgache de la vanille, sur la côte nord-est, entre plages sauvages et "
             "plantations parfumées.",
             -14.2667, 50.1667, 9),
            ("Ambositra", "Amoron'i Mania",
             "Petite ville des Hauts Plateaux réputée pour l'artisanat en marqueterie du peuple "
             "Zafimaniry, classé au patrimoine culturel immatériel de l'UNESCO.",
             -20.5333, 47.2333, 10),
            ("Manakara", "Fitovinany",
             "Ville côtière du sud-est où le Canal des Pangalanes rejoint l'océan Indien — plage, "
             "cocotiers et balades en train historique.",
             -22.1450, 48.0115, 11),
            ("Tolanaro", "Anosy",
             "Fort-Dauphin pour les habitués : plages sauvages, litchis et montagnes, à la pointe sud-est "
             "de l'île.",
             -25.0333, 46.9833, 12),
            ("Moramanga", "Alaotra-Mangoro",
             "Porte d'entrée du parc national d'Andasibe-Mantadia et de ses indris — une aventure nature "
             "à seulement 3h de la capitale.",
             -18.9333, 48.2167, 13),
            ("Ambatolampy", "Vakinankaratra",
             "Petite ville des Hauts Plateaux connue pour ses fondeurs d'aluminium artisanaux et sa "
             "proximité avec le lac de Tsiazompaniry.",
             -19.3833, 47.4333, 14),
        ]
        result = {}
        for name, region, description, lat, lng, order in data:
            city, _ = City.objects.update_or_create(
                name=name,
                defaults={
                    "region": region, "description": description,
                    "latitude": lat, "longitude": lng,
                    "is_active": True, "display_order": order,
                },
            )
            self._download_real_image(city, "image", name, "cities")
            result[name] = city
        return result

    # ------------------------------------------------------------------
    # Catégories
    # ------------------------------------------------------------------

    def _seed_categories(self):
        self.stdout.write("Catégories...")
        data = [
            ("Restaurant", "", 0),
            ("Café & Salon de thé", "", 1),
            ("Bar & Rooftop", "", 2),
            ("Boîte de nuit", "", 3),
            ("Cinéma", "", 4),
            ("Parc & Nature", "", 5),
            ("Plage", "", 6),
            ("Culture & Patrimoine", "", 7),
            ("Spa & Bien-être", "", 8),
        ]
        result = {}
        for name, emoji, order in data:
            cat, _ = Category.objects.update_or_create(
                name=name, defaults={"emoji": emoji, "is_active": True, "display_order": order},
            )
            result[name] = cat
        return result

    # ------------------------------------------------------------------
    # Lieux (réels)
    # ------------------------------------------------------------------

    def _seed_places(self, cities, categories):
        self.stdout.write("Lieux...")

        def C(name):
            return categories[name]

        def V(name):
            return cities[name]

        # (nom, ville, catégorie, quartier, adresse, description courte,
        #  description complète, prix_min, prix_max, note, recommandé, populaire)
        data = [
            # --- Antananarivo -------------------------------------------------
            ("La Varangue", "Antananarivo", "Restaurant", "Antaninarenina",
             "17 Rue Prince Ratsimamanga, Antananarivo 101",
             "Institution gastronomique franco-malgache en plein centre-ville.",
             "Table historique de la capitale, réputée pour sa cuisine franco-malgache raffinée et son "
             "cadre feutré. Un classique pour un dîner aux chandelles à Tana.",
             40000, 90000, 4.5, True, True),
            ("Sakamanga", "Antananarivo", "Restaurant", "Antaninarenina",
             "Rue Rabehevitra, Antananarivo 101",
             "Hôtel-restaurant emblématique à l'ambiance coloniale chaleureuse.",
             "Institution incontournable de Tana depuis des décennies : cour intérieure verdoyante, "
             "décor colonial et cuisine malgache généreuse. Idéal pour une première sortie.",
             25000, 60000, 4.4, True, True),
            ("Le Carnivore", "Antananarivo", "Restaurant", "Ivandry",
             "Lot IVE 67, Ivandry, Antananarivo",
             "Restaurant-bar lounge spécialisé viandes grillées, ambiance conviviale.",
             "Spécialiste de la viande grillée dans une ambiance chaleureuse et animée — service "
             "attentionné et grand choix de plats pour un repas décontracté à deux ou entre amis.",
             25000, 55000, 4.3, False, True),
            ("Nerone Ristorante Italiano", "Antananarivo", "Restaurant", "Ankorondrano",
             "Ankorondrano, Antananarivo",
             "Cuisine italienne authentique dans un cadre élégant.",
             "Pâtes fraîches, pizzas au feu de bois et vins italiens dans une salle chaleureuse — une "
             "valeur sûre pour une soirée en tête-à-tête.",
             30000, 65000, 4.4, False, False),
            ("L'Arrivage", "Antananarivo", "Restaurant", "Ambondrona",
             "Lot DIIF1 Ambondrona, Antananarivo",
             "Bar à huîtres et brasserie de fruits de mer.",
             "Brasserie spécialisée dans les huîtres et produits de la mer, dans une ambiance conviviale "
             "et animée en soirée — parfait pour un apéritif dînatoire à deux.",
             30000, 70000, 4.3, False, False),
            ("Le Rossini", "Antananarivo", "Restaurant", "Antsakaviro",
             "11 Rue Joel Rakotomalala, Antsakaviro, Antananarivo",
             "Cuisine française raffinée dans un cadre intimiste.",
             "Petite table élégante spécialisée en cuisine française, appréciée pour son service "
             "attentionné et son cadre propice aux conversations en tête-à-tête.",
             35000, 75000, 4.2, False, False),
            ("Le Grand Café de la Gare", "Antananarivo", "Café & Salon de thé", "Soarano",
             "Avenue de l'Indépendance, près de la gare de Soarano, Antananarivo",
             "Café-restaurant à l'ambiance vintage près de la gare historique.",
             "Décor de café d'époque près de la gare de Soarano, spécialités locales (romazava, porc "
             "laqué) et service multilingue — un cadre charmant pour un déjeuner à deux.",
             15000, 35000, 4.3, False, True),
            ("Asàra Coffee Shop", "Antananarivo", "Café & Salon de thé", "Ankorondrano",
             "Immeuble Atrium, Ankorondrano, Antananarivo",
             "Coffee shop lifestyle au cœur du quartier d'affaires.",
             "Coffee shop moderne et lumineux, bons cafés de spécialité et pâtisseries — idéal pour un "
             "rendez-vous décontracté en journée.",
             8000, 20000, 4.2, False, False),
            ("Dité", "Antananarivo", "Café & Salon de thé", "Ivandry",
             "Enceinte La City, Ivandry, Antananarivo",
             "Boulangerie-pâtisserie et salon de thé chic.",
             "Salon de thé et boulangerie-pâtisserie apprécié pour ses viennoiseries et son cadre soigné, "
             "au sein du centre La City.",
             8000, 18000, 4.1, False, False),
            ("Pâtisserie Colbert", "Antananarivo", "Café & Salon de thé", "Antaninarenina",
             "29 Rue Prince Ratsimamanga, Antaninarenina, Antananarivo",
             "Institution pâtissière historique de Tana : gâteaux, chocolats, glaces.",
             "Adresse historique pour les gourmands : pâtisseries fines, chocolats et glaces artisanales, "
             "juste à côté de l'Hôtel Colbert.",
             6000, 15000, 4.3, False, True),
            ("No Comment Bar", "Antananarivo", "Bar & Rooftop", "Ampasamadinika",
             "Ampasamadinika, Antananarivo",
             "Bar à cocktails prisé, plus de 70 whiskies et concerts live.",
             "Bar à cocktails populaire connu pour sa caipirinha signature et sa large sélection de "
             "whiskies, avec musique live de groupes et DJ. Ambiance conviviale idéale pour une soirée à deux.",
             15000, 35000, 4.4, True, True),
            ("KUDéTA Urban Club", "Antananarivo", "Boîte de nuit", "Behoririka",
             "Behoririka, Antananarivo",
             "Club branché, DJ sets et piste de danse animée.",
             "Lieu moderne et branché très fréquenté en soirée : musique actuelle, piste de danse animée "
             "et ambiance festive jusqu'au bout de la nuit.",
             20000, 45000, 4.1, False, True),
            ("Le Studio Ivandry", "Antananarivo", "Cinéma", "Ivandry",
             "Route principale Analamahitsy, Ivandry, Antananarivo",
             "Petite salle de cinéma confortable, plus de 2 200 films au catalogue.",
             "Salle de cinéma intimiste d'une vingtaine de fauteuils, très bon confort d'image et de son "
             "— réservation conseillée pour une séance en amoureux.",
             10000, 20000, 4.0, False, False),
            ("CanalOlympia Iarivo", "Antananarivo", "Cinéma", "Ankorondrano",
             "Ankorondrano, Antananarivo",
             "Multiplexe moderne, sorties récentes et confort de salle.",
             "Le grand cinéma moderne de la capitale, avec les dernières sorties et un vrai confort de "
             "salle façon multiplexe — la valeur sûre pour une soirée ciné.",
             12000, 25000, 4.2, True, True),
            ("Institut Français de Madagascar", "Antananarivo", "Culture & Patrimoine", "Analakely",
             "Analakely, Antananarivo",
             "Centre culturel : cinéma d'auteur, expositions, concerts.",
             "Lieu culturel incontournable de Tana : cinéma d'auteur, expositions et concerts dans un "
             "cadre agréable en plein centre-ville.",
             4000, 15000, 4.3, False, False),
            ("Parc de Tsimbazaza", "Antananarivo", "Parc & Nature", "Tsimbazaza",
             "Rue Fernand Kasanga, Tsimbazaza, Antananarivo",
             "Jardin botanique et zoologique, faune endémique de Madagascar.",
             "Parc de 27 hectares fondé en 1925 : jardin botanique, zoo et musée ethnologique organisés "
             "autour d'un lac. L'endroit rêvé pour découvrir lémuriens et plantes endémiques avant de "
             "partir explorer l'île.",
             6000, 12000, 3.9, False, True),
            ("Lac Anosy", "Antananarivo", "Parc & Nature", "Anosy",
             "Avenue de l'Indépendance, Anosy, Antananarivo",
             "Lac artificiel en forme de cœur au centre-ville, promenade romantique.",
             "Oasis paisible en plein centre de la capitale : ce lac en forme de cœur, bordé de "
             "jacarandas, offre un cadre de promenade romantique à toute heure du jour.",
             0, 0, 4.0, True, True),
            ("Rova de Manjakamiadana", "Antananarivo", "Culture & Patrimoine", "Haute-Ville",
             "Colline d'Analamanga, Haute-Ville, Antananarivo",
             "Le palais de la Reine, joyau historique sur la plus haute colline de Tana.",
             "Ancien palais royal des souverains merina, perché sur la plus haute colline de la capitale, "
             "avec une vue imprenable sur toute la ville — une visite chargée d'histoire, parfaite pour "
             "un après-midi culturel à deux.",
             10000, 15000, 4.5, True, False),
            ("Colline Royale d'Ambohimanga", "Antananarivo", "Culture & Patrimoine", "Ambohimanga",
             "Ambohimanga, périphérie d'Antananarivo",
             "Site sacré classé UNESCO, berceau du royaume merina.",
             "Classée au patrimoine mondial de l'UNESCO, cette « colline bleue » aux portes de la "
             "capitale est le berceau du royaume merina — remparts, tombeaux royaux et panorama sur "
             "les rizières environnantes.",
             10000, 15000, 4.6, True, False),
            ("Lemurs Park", "Antananarivo", "Parc & Nature", "Ambatofotsy",
             "Route d'Ambatofotsy, périphérie d'Antananarivo",
             "Parc privé dédié aux lémuriens en semi-liberté.",
             "Havre de verdure à la sortie de Tana, dédié à la préservation des lémuriens : balade "
             "guidée au milieu de plusieurs espèces en semi-liberté, dans un cadre très photogénique.",
             25000, 35000, 4.4, False, False),
            ("Hôtel Carlton Madagascar", "Antananarivo", "Bar & Rooftop", "Anosy",
             "Rue Stibbe, Anosy, Antananarivo",
             "Grand hôtel historique avec bar et vue sur le lac Anosy.",
             "Grand hôtel historique de la capitale, avec un bar élégant offrant l'une des plus belles "
             "vues sur le lac Anosy — idéal pour un cocktail au coucher du soleil.",
             20000, 50000, 4.1, False, False),
            ("Hôtel & Spa Palissandre", "Antananarivo", "Spa & Bien-être", "Andraharo",
             "Andraharo, Antananarivo",
             "Spa haut de gamme, massages et soins en duo.",
             "Spa raffiné proposant massages, hammam et soins en duo dans un cadre zen — la parenthèse "
             "détente parfaite pour un couple avant une soirée en ville.",
             40000, 90000, 4.5, False, False),

            # --- Antsirabe -----------------------------------------------------
            ("Les Thermes d'Antsirabe", "Antsirabe", "Spa & Bien-être", "Centre-ville",
             "Avenue de l'Indépendance, Antsirabe",
             "Établissement thermal historique, bains chauds et détente.",
             "Établissement thermal centenaire, réputé pour ses eaux et son cadre Art déco — un "
             "moment de détente partagée dans la ville thermale des Hauts Plateaux.",
             15000, 35000, 4.0, False, False),
            ("Lac Andraikiba", "Antsirabe", "Parc & Nature", "Périphérie",
             "Route d'Andraikiba, à 7 km d'Antsirabe",
             "Lac de cratère paisible entouré de collines.",
             "Lac de cratère entouré de collines verdoyantes, à quelques minutes du centre : promenade "
             "au bord de l'eau et pique-nique romantique au calme.",
             0, 5000, 4.2, False, False),
            ("Lac Tritriva", "Antsirabe", "Parc & Nature", "Périphérie",
             "Route de Betafo, à 18 km d'Antsirabe",
             "Lac de cratère aux eaux sombres et légendes locales.",
             "Spectaculaire lac de cratère aux parois abruptes et à l'eau presque noire, entouré de "
             "légendes locales sur deux amants maudits — un site aussi mystérieux que romantique.",
             5000, 10000, 4.3, True, False),

            # --- Toamasina -------------------------------------------------
            ("Bazary Be", "Toamasina", "Culture & Patrimoine", "Centre-ville",
             "Centre-ville, Toamasina",
             "Grand marché coloré, artisanat et produits locaux.",
             "Le grand marché historique de Toamasina, effervescent et coloré — épices, artisanat et "
             "produits locaux à découvrir en flânant à deux.",
             0, 20000, 3.9, False, False),
            ("Canal des Pangalanes", "Toamasina", "Parc & Nature", "Bord de mer",
             "Embarcadère du canal, Toamasina",
             "Voie navigable bordée de cocotiers, balade en pirogue.",
             "Long réseau de lagunes et canaux bordés de cocotiers longeant la côte est : une balade en "
             "pirogue ou en petit bateau au coucher du soleil est un classique romantique.",
             15000, 40000, 4.3, True, False),

            # --- Mahajanga -------------------------------------------------
            ("Le Baobab Majunga", "Mahajanga", "Restaurant", "Bord de mer",
             "Avenue de France, bord de mer, Mahajanga",
             "Restaurant en bord de mer, à l'ombre du baobab centenaire.",
             "Restaurant sur le front de mer de Mahajanga, à deux pas du célèbre baobab centenaire — "
             "vue sur le canal du Mozambique et couchers de soleil mémorables.",
             20000, 45000, 4.2, True, False),
            ("Grotte d'Anjohibe", "Mahajanga", "Parc & Nature", "Périphérie",
             "Route d'Anjohibe, à 80 km de Mahajanga",
             "Réseau de grottes calcaires et cascades naturelles.",
             "Impressionnant réseau de grottes calcaires avec stalactites et bassins naturels — une "
             "excursion d'aventure à la journée pour les couples qui aiment sortir des sentiers battus.",
             25000, 50000, 4.1, False, False),

            # --- Fianarantsoa ----------------------------------------------
            ("Vieille Ville Haute de Fianarantsoa", "Fianarantsoa", "Culture & Patrimoine", "Tanana Ambony",
             "Tanana Ambony, Fianarantsoa",
             "Quartier historique escarpé, ruelles pavées et églises anciennes.",
             "Le quartier historique perché de Fianarantsoa : ruelles pavées, maisons traditionnelles "
             "betsileo et églises centenaires, avec une vue superbe sur la ville basse.",
             0, 5000, 4.3, False, False),
            ("Domaine Lazan'i Betsileo", "Fianarantsoa", "Restaurant", "Périphérie",
             "Route de Sahambavy, à 20 km de Fianarantsoa",
             "Domaine viticole malgache, dégustation de vins et repas au vert.",
             "L'un des rares domaines viticoles de Madagascar : visite des vignes, dégustation de vin "
             "malgache et repas au grand air dans un cadre verdoyant.",
             20000, 45000, 4.2, True, False),

            # --- Toliara ---------------------------------------------------
            ("Plage d'Ifaty", "Toliara", "Plage", "Ifaty",
             "Route d'Ifaty, à 25 km de Toliara",
             "Plage de sable blanc et récifs coralliens, snorkeling.",
             "Longue plage de sable blanc bordée de baobabs, célèbre pour ses récifs coralliens juste "
             "au large — snorkeling, farniente et coucher de soleil sur le canal du Mozambique.",
             0, 15000, 4.5, True, True),
            ("Arboretum d'Antsokay", "Toliara", "Parc & Nature", "Périphérie",
             "Route de Tuléar, à 12 km de Toliara",
             "Jardin botanique dédié à la flore endémique du sud aride.",
             "Jardin botanique unique dédié à la végétation épineuse du sud de Madagascar — baobabs, "
             "plantes endémiques et visite guidée passionnante pour les amoureux de nature.",
             10000, 20000, 4.3, False, False),

            # --- Antsiranana (Diego Suarez) ---------------------------------
            ("Mer d'Émeraude", "Antsiranana", "Plage", "Baie de Diego",
             "Baie de Diego-Suarez, Antsiranana",
             "Lagon turquoise peu profond, snorkeling et pique-nique sur banc de sable.",
             "Lagon aux eaux turquoise peu profondes, accessible en pirogue depuis Ramena — snorkeling, "
             "pique-nique sur un banc de sable et coucher de soleil spectaculaire.",
             30000, 60000, 4.6, True, True),
            ("Tsingy Rouges", "Antsiranana", "Parc & Nature", "Périphérie",
             "Route d'Irodo, à 50 km d'Antsiranana",
             "Formations rocheuses érodées aux couleurs flamboyantes.",
             "Étonnantes formations de latérite érodée, rouges et orangées, qui se révèlent surtout en "
             "fin de journée — un décor spectaculaire pour une excursion d'aventure à deux.",
             20000, 40000, 4.4, False, False),

            # --- Nosy Be -----------------------------------------------------
            ("Plage d'Andilana", "Nosy Be", "Plage", "Andilana",
             "Nord-ouest de l'île, Nosy Be",
             "La plage la plus célèbre de l'île, eau calme et sable blanc.",
             "Considérée comme la plus belle plage de Nosy Be : sable blanc, eau calme et turquoise, "
             "idéale pour la baignade et le snorkeling au coucher du soleil.",
             0, 10000, 4.6, True, True),
            ("Mont Passot", "Nosy Be", "Parc & Nature", "Centre de l'île",
             "Route du Mont Passot, Nosy Be",
             "Point culminant de l'île, vue panoramique sur les lacs volcaniques.",
             "Le point culminant de Nosy Be, offrant une vue à 360° sur les lacs de cratère sacrés et "
             "l'océan Indien — un des plus beaux couchers de soleil de l'île.",
             15000, 25000, 4.5, True, False),
            ("Restaurant Chez Loulou", "Nosy Be", "Restaurant", "Ambatoloaka",
             "Plage d'Ambatoloaka, Nosy Be",
             "Restaurant les pieds dans le sable, spécialités de fruits de mer.",
             "Table réputée en bord de plage, spécialisée dans les fruits de mer et le poisson grillé "
             "— dîner les pieds dans le sable au son des vagues.",
             25000, 55000, 4.4, False, True),

            # --- Morondava ---------------------------------------------------
            ("Allée des Baobabs", "Morondava", "Parc & Nature", "Route de Morondava",
             "Route nationale 8, à 20 km de Morondava",
             "Site naturel emblématique de Madagascar, coucher de soleil mythique.",
             "L'un des paysages les plus photographiés de Madagascar : une rangée de baobabs "
             "centenaires bordant la piste, embrasés par la lumière du coucher de soleil — un moment "
             "immanquable pour un couple en voyage.",
             10000, 20000, 4.8, True, True),
            ("Baobab Amoureux", "Morondava", "Parc & Nature", "Route de Morondava",
             "À proximité de l'Allée des Baobabs, Morondava",
             "Deux baobabs entrelacés, symbole d'amour éternel.",
             "Deux troncs de baobabs qui s'enlacent en une spirale naturelle unique au monde — un "
             "symbole d'amour éternel très prisé des couples en photo souvenir.",
             5000, 10000, 4.6, True, False),

            # --- Sambava -----------------------------------------------------
            ("Plage de Sambava", "Sambava", "Plage", "Front de mer",
             "Front de mer, Sambava",
             "Longue plage sauvage bordée de cocotiers.",
             "Immense plage de sable fin peu fréquentée, parfaite pour une longue marche en amoureux "
             "au coucher du soleil, à deux pas des plantations de vanille.",
             0, 5000, 4.2, False, False),

            # --- Ambositra ---------------------------------------------------
            ("Village artisanal Zafimaniry", "Ambositra", "Culture & Patrimoine", "Centre-ville",
             "Centre-ville, Ambositra",
             "Ateliers de marqueterie sur bois, savoir-faire classé UNESCO.",
             "Ateliers d'artisans travaillant le bois précieux en marqueterie fine, un savoir-faire "
             "classé au patrimoine immatériel de l'UNESCO — une visite culturelle et shopping à la fois.",
             0, 30000, 4.1, False, False),

            # --- Manakara ------------------------------------------------------
            ("Plage de Manakara", "Manakara", "Plage", "Front de mer",
             "Front de mer, Manakara",
             "Plage tranquille où le Canal des Pangalanes rejoint l'océan.",
             "Plage paisible bordée de cocotiers, à l'endroit précis où le Canal des Pangalanes se "
             "jette dans l'océan Indien — coucher de soleil et fruits de mer grillés au programme.",
             0, 10000, 4.0, False, False),

            # --- Tolanaro (Fort-Dauphin) -------------------------------------
            ("Plage de Libanona", "Tolanaro", "Plage", "Libanona",
             "Presqu'île de Libanona, Tolanaro",
             "Anse spectaculaire entourée de montagnes.",
             "Anse de sable blanc nichée entre deux caps rocheux, l'une des plus belles baies du sud "
             "de Madagascar — parfaite pour une baignade tranquille à deux.",
             0, 8000, 4.4, False, False),

            # --- Moramanga -----------------------------------------------------
            ("Parc National Andasibe-Mantadia", "Moramanga", "Parc & Nature", "Andasibe",
             "Andasibe, à 25 km de Moramanga",
             "Forêt tropicale, chant de l'indri indri au lever du jour.",
             "L'une des expériences nature les plus fortes de Madagascar : partir à l'aube entendre le "
             "chant si particulier de l'indri indri, le plus grand des lémuriens, au cœur d'une forêt "
             "tropicale préservée.",
             40000, 70000, 4.7, True, True),

            # --- Ambatolampy ------------------------------------------------
            ("Lac de Tsiazompaniry", "Ambatolampy", "Parc & Nature", "Périphérie",
             "Route de Tsiazompaniry, à 25 km d'Ambatolampy",
             "Grand lac de retenue entouré de collines, pique-nique au calme.",
             "Vaste plan d'eau entouré de collines verdoyantes, loin de l'agitation de la capitale — "
             "cadre paisible pour un pique-nique ou une balade en amoureux.",
             0, 10000, 4.0, False, False),
        ]

        result = {}
        for (name, city_name, cat_name, neighborhood, address, short_desc,
             full_desc, price_min, price_max, rating, is_recommended, is_popular) in data:
            place, _ = Place.objects.update_or_create(
                name=name,
                defaults={
                    "city": V(city_name), "category": C(cat_name),
                    "neighborhood": neighborhood, "address": address,
                    "short_description": short_desc, "full_description": full_desc,
                    "price_min": price_min, "price_max": price_max, "rating": rating,
                    "is_recommended": is_recommended, "is_popular": is_popular,
                    "is_active": True,
                },
            )
            self._download_real_image(place, "main_image", name, "places")
            result[name] = place
        return result

    # ------------------------------------------------------------------
    # Ambiances / Budgets / Occasions
    # ------------------------------------------------------------------

    def _seed_moods(self):
        self.stdout.write("Ambiances...")
        data = [
            ("Romantique", "", "Dîners aux chandelles, couchers de soleil et têtes-à-tête.", 0),
            ("Fun", "", "Rires garantis : jeux, karaoké, sorties animées.", 1),
            ("Chill", "", "Détente, calme et conversations tranquilles.", 2),
            ("Aventure", "", "Sensations fortes et sorties qui sortent de l'ordinaire.", 3),
            ("Nature", "", "Grand air, verdure et paysages malgaches.", 4),
            ("Festif", "", "Musique, danse et ambiance de fête.", 5),
        ]
        result = {}
        for name, emoji, desc, order in data:
            mood, _ = Mood.objects.update_or_create(
                name=name, defaults={"emoji": emoji, "description": desc, "is_active": True, "display_order": order},
            )
            result[name] = mood
        return result

    def _seed_budgets(self):
        self.stdout.write("Budgets...")
        data = [
            ("Petit budget", 0, 30000, 0),
            ("Budget moyen", 30000, 80000, 1),
            ("Confort", 80000, 150000, 2),
            ("Premium", 150000, None, 3),
        ]
        result = {}
        for label, min_a, max_a, order in data:
            budget, _ = Budget.objects.update_or_create(
                label=label, defaults={"min_amount": min_a, "max_amount": max_a, "is_active": True, "display_order": order},
            )
            result[label] = budget
        return result

    def _seed_occasions(self):
        self.stdout.write("Occasions...")
        data = [
            ("Premier rendez-vous", "", "On se rencontre pour la première fois.", 0),
            ("Anniversaire", "", "Fêter un anniversaire de naissance.", 1),
            ("Anniversaire de couple", "", "Célébrer une date importante du couple.", 2),
            ("Retrouvailles", "", "Se retrouver après un moment sans se voir.", 3),
            ("Demande en couple", "", "Officialiser une relation naissante.", 4),
            ("Demande en mariage", "", "Le grand jour de la demande.", 5),
            ("Sortie sans occasion particulière", "", "Juste envie de passer un bon moment ensemble.", 6),
        ]
        for name, emoji, desc, order in data:
            Occasion.objects.update_or_create(
                name=name, defaults={"emoji": emoji, "description": desc, "is_active": True, "display_order": order},
            )

    # ------------------------------------------------------------------
    # Activités
    # ------------------------------------------------------------------

    def _seed_activities(self, cities, places, categories, moods, budgets):
        self.stdout.write("Activités...")

        def M(*names):
            return [moods[n] for n in names]

        def B(*labels):
            return [budgets[l] for l in labels]

        # (nom, ville, lieu, catégorie, description, durée_min, prix, moods, budgets)
        data = [
            ("Dîner aux chandelles à La Varangue", "Antananarivo", "La Varangue", "Restaurant",
             "Un dîner gastronomique franco-malgache dans le cadre feutré de l'une des tables les plus "
             "réputées de la capitale.", 120, 70000, M("Romantique"), B("Confort", "Premium")),
            ("Cocktails au rooftop du Carlton", "Antananarivo", "Hôtel Carlton Madagascar", "Bar & Rooftop",
             "Un verre au coucher du soleil avec vue sur le lac Anosy, dans le cadre élégant de "
             "l'hôtel historique.", 90, 30000, M("Romantique", "Chill"), B("Budget moyen", "Confort")),
            ("Séance ciné au CanalOlympia", "Antananarivo", "CanalOlympia Iarivo", "Cinéma",
             "Une sortie cinéma classique dans le multiplexe le plus moderne de Tana.",
             150, 18000, M("Fun", "Chill"), B("Petit budget", "Budget moyen")),
            ("Balade et pique-nique à Tsimbazaza", "Antananarivo", "Parc de Tsimbazaza", "Parc & Nature",
             "Promenade au milieu de la faune endémique malgache, entre lac et arboretum.",
             150, 10000, M("Nature", "Chill"), B("Petit budget")),
            ("Coucher de soleil au Lac Anosy", "Antananarivo", "Lac Anosy", "Parc & Nature",
             "Une balade romantique au bord du lac en forme de cœur, en plein centre-ville.",
             60, 0, M("Romantique", "Chill"), B("Petit budget")),
            ("Visite du Rova de Manjakamiadana", "Antananarivo", "Rova de Manjakamiadana", "Culture & Patrimoine",
             "Visite du palais de la Reine et panorama sur toute la capitale.",
             90, 12000, M("Nature", "Chill"), B("Petit budget", "Budget moyen")),
            ("Excursion à la Colline Royale d'Ambohimanga", "Antananarivo", "Colline Royale d'Ambohimanga", "Culture & Patrimoine",
             "Excursion à la demi-journée sur le site sacré classé UNESCO, aux portes de la capitale.",
             240, 25000, M("Nature", "Aventure"), B("Budget moyen", "Confort")),
            ("Soirée cocktails au No Comment Bar", "Antananarivo", "No Comment Bar", "Bar & Rooftop",
             "Cocktails signature et musique live dans l'un des bars les plus courus de Tana.",
             150, 25000, M("Festif", "Fun"), B("Budget moyen")),
            ("Soirée clubbing au KUDéTA", "Antananarivo", "KUDéTA Urban Club", "Boîte de nuit",
             "DJ sets et piste de danse jusqu'au bout de la nuit.",
             180, 30000, M("Festif", "Fun"), B("Budget moyen", "Confort")),
            ("Spa en duo au Palissandre", "Antananarivo", "Hôtel & Spa Palissandre", "Spa & Bien-être",
             "Massage en duo et moment de détente complet dans un cadre haut de gamme.",
             120, 65000, M("Chill", "Romantique"), B("Confort", "Premium")),
            ("Balade en pousse-pousse à Antsirabe", "Antsirabe", None, "Culture & Patrimoine",
             "Balade typique en pousse-pousse dans les rues d'Antsirabe, la ville thermale.",
             60, 8000, M("Fun", "Chill"), B("Petit budget")),
            ("Baignade thermale à Antsirabe", "Antsirabe", "Les Thermes d'Antsirabe", "Spa & Bien-être",
             "Détente dans les bains chauds de l'établissement thermal historique.",
             90, 25000, M("Chill", "Romantique"), B("Budget moyen", "Confort")),
            ("Pique-nique au Lac Andraikiba", "Antsirabe", "Lac Andraikiba", "Parc & Nature",
             "Pique-nique au calme au bord du lac de cratère, à quelques minutes du centre.",
             120, 8000, M("Nature", "Romantique"), B("Petit budget")),
            ("Balade en pirogue sur le Canal des Pangalanes", "Toamasina", "Canal des Pangalanes", "Parc & Nature",
             "Balade en pirogue au coucher du soleil sur les lagunes bordées de cocotiers.",
             120, 25000, M("Romantique", "Nature"), B("Budget moyen")),
            ("Dégustation de vin au Domaine Lazan'i Betsileo", "Fianarantsoa", "Domaine Lazan'i Betsileo", "Restaurant",
             "Visite du vignoble et dégustation de vins malgaches dans un cadre verdoyant.",
             150, 30000, M("Romantique", "Chill"), B("Budget moyen", "Confort")),
            ("Snorkeling à Ifaty", "Toliara", "Plage d'Ifaty", "Plage",
             "Découverte des récifs coralliens en snorkeling, face à la plage de sable blanc.",
             180, 20000, M("Aventure", "Nature"), B("Budget moyen")),
            ("Excursion à la Mer d'Émeraude", "Antsiranana", "Mer d'Émeraude", "Plage",
             "Traversée en pirogue vers le lagon turquoise, pique-nique sur banc de sable.",
             240, 45000, M("Aventure", "Romantique"), B("Confort")),
            ("Farniente à Andilana", "Nosy Be", "Plage d'Andilana", "Plage",
             "Journée farniente sur la plus belle plage de l'île, baignade et snorkeling.",
             240, 15000, M("Chill", "Romantique"), B("Petit budget", "Budget moyen")),
            ("Coucher de soleil au Mont Passot", "Nosy Be", "Mont Passot", "Parc & Nature",
             "Montée au point culminant de l'île pour admirer le coucher de soleil sur les lacs sacrés.",
             90, 20000, M("Romantique", "Aventure"), B("Budget moyen")),
            ("Coucher de soleil à l'Allée des Baobabs", "Morondava", "Allée des Baobabs", "Parc & Nature",
             "L'un des couchers de soleil les plus célèbres du monde, au milieu des baobabs centenaires.",
             90, 15000, M("Romantique", "Nature"), B("Petit budget", "Budget moyen")),
            ("Trek à l'écoute des indris à Andasibe", "Moramanga", "Parc National Andasibe-Mantadia", "Parc & Nature",
             "Randonnée matinale en forêt tropicale à l'écoute du chant des indris.",
             180, 55000, M("Aventure", "Nature"), B("Confort", "Premium")),
        ]

        result = {}
        for row in data:
            (name, city_name, place_name, cat_name, desc, duration, price, mood_list, budget_list) = row
            activity, _ = Activity.objects.update_or_create(
                name=name,
                defaults={
                    "city": cities[city_name],
                    "place": places[place_name] if place_name else None,
                    "category": categories[cat_name],
                    "description": desc,
                    "duration_minutes": duration,
                    "price": price,
                    "is_active": True,
                },
            )
            activity.compatible_moods.set(mood_list)
            activity.compatible_budgets.set(budget_list)
            self._download_real_image(activity, "image", name, "activities")
            result[name] = activity
        return result

    # ------------------------------------------------------------------
    # Packages clé en main
    # ------------------------------------------------------------------

    def _seed_packages(self, cities, places, activities, moods, budgets):
        self.stdout.write("Packages...")
        # (nom, ville, lieu, activité, mood, budget, description, prix, featured)
        data = [
            ("Soirée romantique à La Varangue", "Antananarivo", "La Varangue",
             "Dîner aux chandelles à La Varangue", "Romantique", "Confort",
             "Un dîner gastronomique dans l'une des meilleures tables de la capitale, suivi d'une "
             "balade au clair de lune. Le classique indémodable pour une soirée en tête-à-tête.",
             70000, True),
            ("Ciné & cocktails à Tana", "Antananarivo", "CanalOlympia Iarivo",
             "Séance ciné au CanalOlympia", "Fun", "Budget moyen",
             "Une séance dans le meilleur multiplexe de la ville, suivie d'un verre dans un bar branché "
             "du quartier — une soirée simple et efficace.",
             35000, False),
            ("Journée nature à Tsimbazaza", "Antananarivo", "Parc de Tsimbazaza",
             "Balade et pique-nique à Tsimbazaza", "Nature", "Petit budget",
             "Une après-midi tranquille à la découverte de la faune malgache, entre lac et jardin "
             "botanique — parfait pour un premier rendez-vous décontracté.",
             12000, False),
            ("Escapade royale à Ambohimanga", "Antananarivo", "Colline Royale d'Ambohimanga",
             "Excursion à la Colline Royale d'Ambohimanga", "Nature", "Budget moyen",
             "Une demi-journée hors de la ville sur le site sacré classé UNESCO, entre histoire royale "
             "et panorama sur les rizières.",
             25000, False),
            ("Nuit électrique à Tana", "Antananarivo", "No Comment Bar",
             "Soirée cocktails au No Comment Bar", "Festif", "Budget moyen",
             "Cocktails signature, musique live et ambiance survoltée pour une soirée qui sort de "
             "l'ordinaire.",
             28000, False),
            ("Week-end thermal à Antsirabe", "Antsirabe", "Les Thermes d'Antsirabe",
             "Baignade thermale à Antsirabe", "Chill", "Confort",
             "Une escapade sur les Hauts Plateaux : bains thermaux, balade en pousse-pousse et pique-"
             "nique au bord d'un lac de cratère.",
             45000, True),
            ("Coucher de soleil sur les Baobabs", "Morondava", "Allée des Baobabs",
             "Coucher de soleil à l'Allée des Baobabs", "Romantique", "Petit budget",
             "L'un des couchers de soleil les plus mythiques du monde, au cœur de l'Allée des Baobabs "
             "— un souvenir de voyage inoubliable à deux.",
             15000, True),
            ("Farniente à Nosy Be", "Nosy Be", "Plage d'Andilana",
             "Farniente à Andilana", "Chill", "Budget moyen",
             "Une journée complète sur la plus belle plage de l'île aux parfums : baignade, snorkeling "
             "et déjeuner les pieds dans le sable.",
             35000, True),
            ("Aventure Émeraude à Diego", "Antsiranana", "Mer d'Émeraude",
             "Excursion à la Mer d'Émeraude", "Aventure", "Confort",
             "Traversée en pirogue vers le lagon turquoise le plus photographié du nord de Madagascar, "
             "pique-nique sur un banc de sable inclus.",
             50000, False),
            ("Aventure indris à Andasibe", "Moramanga", "Parc National Andasibe-Mantadia",
             "Trek à l'écoute des indris à Andasibe", "Aventure", "Premium",
             "Une expédition nature inoubliable à 3h de la capitale : randonnée matinale en forêt "
             "tropicale pour entendre le chant si particulier des indris.",
             60000, False),
        ]
        for name, city_name, place_name, activity_name, mood_name, budget_label, desc, price, featured in data:
            package, _ = DatePackage.objects.update_or_create(
                name=name,
                defaults={
                    "city": cities[city_name],
                    "place": places.get(place_name),
                    "activity": activities.get(activity_name),
                    "mood": moods.get(mood_name),
                    "budget": budgets.get(budget_label),
                    "description": desc,
                    "price_estimate": price,
                    "is_featured": featured,
                    "is_active": True,
                },
            )
            self._download_real_image(package, "image", name, "packages")

    # ------------------------------------------------------------------
    # Configuration du site
    # ------------------------------------------------------------------

    def _seed_site_config(self):
        self.stdout.write("Configuration du site...")
        config = SiteConfiguration.load()
        config.site_name = "Date With U"
        config.contact_email = "contact@datewithu.mg"
        config.contact_phone = "+261 34 00 000 00"
        config.default_currency = "MGA"
        config.invitation_expiration_days = 7
        config.registration_enabled = True
        config.chat_enabled = True
        config.reviews_enabled = True
        config.save()

    # ------------------------------------------------------------------
    # Magazine (articles de blog) et formules Premium
    # ------------------------------------------------------------------

    def _seed_blog(self, cities):
        self.stdout.write("Articles du magazine...")
        from apps.blog.models import Article

        data = [
            ("10 spots romantiques à Antananarivo pour un premier rendez-vous", "Antananarivo",
             "De la terrasse du Carlton au coucher de soleil sur le Lac Anosy : notre sélection "
             "pour une première sortie réussie dans la capitale.",
             "## Le Lac Anosy, au coucher du soleil\n"
             "Ce lac en forme de cœur en plein centre-ville reste un classique pour une bonne raison : "
             "c'est gratuit, romantique, et à deux pas de tout.\n\n"
             "## La Varangue, pour un dîner qui marque les esprits\n"
             "Cuisine franco-malgache raffinée dans un cadre feutré — l'adresse à garder pour une "
             "occasion spéciale.\n\n"
             "## Le rooftop du Carlton\n"
             "Un cocktail avec vue sur la ville, parfait pour prolonger la soirée en douceur.\n\n"
             "**Le conseil Date With U** : réserve toujours à l'avance le week-end, ces adresses sont prisées."),
            ("Allée des Baobabs : pourquoi c'est LE coucher de soleil à vivre à deux", "Morondava",
             "L'un des paysages les plus photographiés du monde se trouve à Madagascar. Voici comment "
             "en profiter pleinement.",
             "## Un décor unique au monde\n"
             "Cette rangée de baobabs centenaires, embrasée par la lumière du soir, est un spectacle "
             "que peu de couples oublient.\n\n"
             "## Le bon moment\n"
             "Arrivez environ 45 minutes avant le coucher du soleil pour trouver un bon emplacement et "
             "profiter de la lumière dorée qui précède le spectacle.\n\n"
             "- Prévoyez de l'eau, il fait chaud en journée\n"
             "- Le Baobab Amoureux se trouve à quelques minutes, à ne pas manquer\n"
             "- Repartez un peu avant la nuit noire, la piste n'est pas éclairée"),
            ("Week-end à Nosy Be : notre itinéraire romantique", "Nosy Be",
             "Plages, couchers de soleil et îles voisines : de quoi remplir un week-end en amoureux "
             "sur l'île aux parfums.",
             "## Jour 1 : farniente à Andilana\n"
             "La plus belle plage de l'île pour une arrivée en douceur — sable blanc et eau turquoise.\n\n"
             "## Jour 2 : Mont Passot puis Nosy Komba\n"
             "Levez-vous tôt pour le panorama depuis le Mont Passot, puis direction Nosy Komba "
             "pour observer les lémuriens en semi-liberté.\n\n"
             "**Bon plan** : réservez votre transport en pirogue la veille, les départs sont plus "
             "fréquents en matinée."),
            ("Petit budget, grande sortie : nos idées à moins de 20 000 Ar", None,
             "Un rendez-vous réussi n'a pas besoin d'être cher — la preuve avec cette sélection.",
             "## Pique-nique au Parc de Tsimbazaza\n"
             "Entrée à petit prix, cadre verdoyant et faune endémique à découvrir à deux.\n\n"
             "## Balade au Lac Anosy\n"
             "Toujours gratuit, toujours efficace pour une balade en fin de journée.\n\n"
             "## Marché et street-food\n"
             "Flânez dans un marché local et goûtez ensemble aux spécialités de rue — convivial et "
             "économique.\n\n"
             "**Astuce** : utilise le filtre budget « Petit budget » dans le Date Builder pour ne voir "
             "que ce genre d'options."),
        ]
        for title, city_name, excerpt, content in data:
            Article.objects.update_or_create(
                title=title,
                defaults={
                    "excerpt": excerpt,
                    "content": content,
                    "city": cities.get(city_name) if city_name else None,
                    "is_published": True,
                },
            )

    def _seed_premium_plans(self):
        self.stdout.write("Formules Premium...")
        from apps.premium.models import PremiumPlan

        data = [
            ("Premium mensuel", 15000, 30,
             "Rendez-vous illimités\nBadge Premium sur le profil\nAccès prioritaire aux nouveaux lieux\nSupport prioritaire"),
            ("Premium annuel", 150000, 365,
             "Tous les avantages du mensuel\n2 mois offerts par rapport au mensuel\nBadge Premium annuel"),
        ]
        for order, (name, price, duration, perks) in enumerate(data):
            PremiumPlan.objects.update_or_create(
                name=name,
                defaults={
                    "price": price, "duration_days": duration,
                    "perks": perks, "is_active": True, "display_order": order,
                },
            )
