"""Texte du guide en français (parties I à III). La partie IV, référence des fonctions, est faite à partir
du code par docs/make_guide_odt.py, avec les explications de reference_fr.py et reference_fr_more.py.

Blocs : ("h1"|"h2"|"h3", titre), ("p", texte), ("ul"|"ol", [éléments]), ("code", texte),
("tip"|"warn"|"note", texte), ("table", [ligne d'en-tête, lignes…]), ("figure", image, légende),
("defs", [(terme, définition)…]), ("annotated", fichier, fonction, [explication de chaque ligne]), ("pagebreak",).
Dans les textes : **gras**, *italique*, `code`."""

TITLE = "Gerbil"
SUBTITLE = "Guide de l'archéologue et du code"
TAGLINE = "Détourer, mesurer, publier : utiliser Gerbil et comprendre ce qu'il fait, fonction par fonction"
FOOTER = "Gerbil — Guide de l'archéologue et du code"
LABELS = {
    "contents": "Sommaire", "foreword": "Avant-propos", "line": "ligne", "lines": "lignes", "function": "fonction", "class": "classe",
    "method": "méthode", "untranslated": "(à traduire)", "helper": "(petite fonction utilitaire : voir le code)",
    "tip": "Astuce", "warn": "Attention", "note": "À savoir", "code_col": "Code", "expl_col": "Ce que fait la ligne",
    "part4": "Partie IV — Référence des fonctions, fichier par fichier",
    "part4_intro": "Chaque fichier du programme, ses sections (les bandeaux « # ---- » du code) et, dans chacune, "
        "toutes ses fonctions et classes, avec leur explication et leur numéro de ligne dans le fichier. Le "
        "nom écrit en violet est celui que l'on cherche dans le code (Ctrl+F) ; entre parenthèses, ce que la "
        "fonction reçoit.",
    "generated": "Cette partie est écrite automatiquement à partir du code (docs/make_guide_odt.py) : elle suit "
        "toujours la version du programme.",
    "version": "Version", "licence": "Logiciel libre sous licence GNU GPL v3 ou ultérieure",
    "date": "Guide produit le",
}
FILE_ROLES = {
    "gerbil.py": "Le moteur et la ligne de commande : tout ce qui traite une photo.",
    "gerbil_gui.pyw": "L'interface (les fenêtres) : elle lance le moteur comme un programme séparé.",
    "gerbil_plates.py": "Les planches : objets mis en page à une échelle choisie, écrits en SVG.",
    "gerbil_tools.py": "L'inventaire (CSV) et les vignettes.",
    "packaging/gerbil_setup.pyw": "L'installateur (Gerbil_Setup.exe).",
    "tests/synthetic.py": "Les photos synthétiques des tests automatiques.",
    "tests/test_gerbil.py": "Les tests automatiques.",
}

SECTION_TITLES = {
    "Image and metadata loading": "Lecture des images et des métadonnées",
    "Background model and \"object / background\" map": "Modèle du fond et carte « objet / fond »",
    "Scale detection and measurement (squares)": "Détection et mesure de l'échelle (cases)",
    "Site profiles and learned scales": "Profils de site et échelles apprises",
    "Graduated ruler (millimetre ticks on a light card)": "Réglet gradué (graduations millimétriques sur carton clair)",
    "Ceramic outlining": "Détourage de l'objet",
    "AI second opinion (optional, --ai): neural segmentation of the object":
        "Second avis de l'IA (option --ai) : segmentation de l'objet par un réseau de neurones",
    "One-click cut-out (review window): Segment Anything, MobileSAM version":
        "Détourage en un clic (fenêtre de vérification) : Segment Anything, version MobileSAM",
    "Layers and compositing": "Calques et fusion",
    "PSD writing (layers, layer masks, resolution, ICC profile, EXIF)":
        "Écriture du PSD (calques, masques de fusion, résolution, profil ICC, EXIF)",
    "TIFF writing": "Écriture des TIFF",
    "Control preview": "Aperçu de contrôle",
    "Processing of one photo": "Traitement d'une photo",
    "Project: fields, naming template, naming rule, values of the photos (gerbil_project.json)":
        "Projet : champs, modèle de nom, règle de nommage, valeurs des photos (gerbil_project.json)",
    "Review window: data written for it, corrections read back":
        "Fenêtre de vérification : données écrites pour elle, corrections relues",
    "Objects of a results folder": "Les objets d'un dossier de résultats",
    "Drawing: shapes in millimetres, written as SVG or drawn with Pillow":
        "Drawing : formes en millimètres, écrites en SVG ou dessinées avec Pillow",
    "Scale bar": "Barre d'échelle",
    "Drawings (vector: SVG, or .ai / .pdf / .eps converted by Inkscape)":
        "Dessins (vectoriels : SVG, ou .ai / .pdf / .eps convertis par Inkscape)",
    "Layout": "Mise en page",
}

FOREWORD = [
    ("p", "Gerbil détoure les objets archéologiques photographiés avec une échelle et les restitue **à leur "
          "taille réelle** : glissés dans Illustrator, ils s'affichent au 1:1, sans calcul ni mise à l'échelle "
          "à la main. Il prépare aussi les planches, les noms de fichiers, les métadonnées et les inventaires."),
    ("p", "Ce guide s'adresse à la fois à ceux qui **utilisent** Gerbil et à ceux qui veulent **comprendre** ce "
          "qu'il fait, pour l'expliquer dans un rapport, le vérifier ou le modifier. Il se lit dans l'ordre que "
          "l'on veut :"),
    ("ul", ["**Partie I — Utiliser Gerbil** : de l'installation aux planches, pas à pas.",
            "**Partie II — Comprendre les traitements** : chaque étape expliquée en mots simples, avec les seuils "
            "et les mesures de précision ; de quoi rédiger une méthodologie.",
            "**Partie III — Lire le code** : comment le programme est organisé, les notions de Python utiles, et "
            "des fonctions réelles commentées ligne par ligne.",
            "**Partie IV — Référence** : toutes les fonctions et classes du programme (plus de 400), expliquées "
            "en français, avec leur numéro de ligne."]),
    ("note", "L'interface de Gerbil est pour l'instant en anglais : les noms des boutons et des options sont "
             "donnés ici tels qu'ils apparaissent à l'écran (*Add folder…*, *Run*…), avec leur explication en "
             "français."),
]

PARTS = [
    # =========================================================================================== PARTIE I
    ("h1", "Partie I — Utiliser Gerbil"),

    ("h2", "1. Ce que fait Gerbil"),
    ("p", "On donne à Gerbil un dossier de photos d'objets (tessons, métal, lithique, os, verre…) posés sur un "
          "fond uni avec une échelle. Pour chaque photo, il :"),
    ("ol", ["**trouve l'échelle** (damier noir / blanc / rouge, rangée simple ou réglet millimétré) et la mesure : "
            "combien de pixels font un centimètre sur *cette* photo ;",
            "**détoure l'objet** : il le sépare du fond, écarte les étiquettes, les supports, les chartes couleur "
            "et l'échelle elle-même ;",
            "**écrit les fichiers** : un PSD à calques et des TIFF transparents dont la résolution est la vraie, "
            "pour que l'objet s'affiche à sa taille réelle dans Illustrator, Photoshop ou InDesign ;",
            "**signale ses doutes** : tout ce qui mérite un coup d'œil reçoit le suffixe `_to_be_verified`."]),
    ("p", "La mesure vient de l'échelle de chaque photo, pas des données EXIF : l'appareil, l'objectif et la "
          "distance de prise de vue n'ont aucune importance. Une photo prise de plus près donne simplement plus "
          "de pixels par centimètre."),
    ("figure", "fig_photo", "Une photo à traiter (photo synthétique : un tesson inventé et une échelle à damier de "
                            "10 cm)."),

    ("h2", "2. Installer Gerbil"),
    ("h3", "Sur un ordinateur sans Python (le plus simple)"),
    ("ol", ["Double-cliquer sur **Gerbil_Setup.exe** (un seul fichier, environ 100 Mo).",
            "Garder le dossier proposé (pas besoin des droits d'administrateur) et cocher, si on veut, le "
            "raccourci sur le bureau, puis *Install*.",
            "Ouvrir Gerbil depuis le menu Démarrer."]),
    ("warn", "Les programmes ne sont pas signés : au premier lancement, Windows peut afficher « Windows a protégé "
             "votre ordinateur ». Cliquer sur *Informations complémentaires*, puis *Exécuter quand même*."),
    ("p", "Pour mettre à jour, il suffit de lancer un Gerbil_Setup.exe plus récent : les modèles d'IA déjà "
          "téléchargés sont gardés. Pour désinstaller : *Paramètres > Applications > Applications installées*. "
          "Les photos et les résultats ne sont jamais touchés."),
    ("h3", "Avec les scripts Python"),
    ("p", "Copier tout le dossier du programme, double-cliquer une fois sur **Install.bat** (il installe Python "
          "si besoin, puis numpy, OpenCV, Pillow et rawpy), puis ouvrir l'interface avec **Gerbil.bat**."),

    ("h2", "3. Bien prendre les photos"),
    ("ul", ["**L'échelle dans le plan de l'objet** : à la même hauteur que la face photographiée. Une échelle posée "
            "sur la table sous un objet épais donne une mesure fausse (l'objet est plus près de l'objectif).",
            "**Un fond uni** et différent de l'objet : clair (la situation prévue) ou sombre (velours noir, "
            "feutre). Un léger dégradé d'éclairage ne gêne pas.",
            "**Une échelle reconnue** : damier noir / blanc / rouge de 5, 10 ou 20 cm (une ou deux rangées, "
            "chiffres imprimés dans les cases acceptés), rangée simple noire et blanche, ou réglet gradué en "
            "millimètres. Une autre échelle peut être *apprise* (voir les profils de site).",
            "**L'objet entier dans le cadre**, sans toucher le bord de la photo.",
            "**Formats** : JPEG, TIFF, PNG ou RAW (DNG, CR2, CR3, NEF, ARW, ORF, RW2, RAF…)."]),
    ("tip", "Pâte à fixe : une pâte bleue (type Blu-Tack), ou cachée derrière l'objet, évite qu'elle soit "
            "confondue avec un tesson clair."),

    ("h2", "4. Premier traitement, pas à pas"),
    ("ol", ["Ouvrir Gerbil.",
            "*Add folder…* : choisir le dossier des photos (le nombre de photos s'affiche). On peut en ajouter "
            "plusieurs, ou glisser des dossiers sur la fenêtre.",
            "Laisser les options par défaut pour un premier essai. Laisser la souris sur une option affiche son "
            "explication.",
            "Cliquer sur **Run**. Le journal affiche chaque photo : en vert si tout va bien, en terre cuite si elle "
            "est à vérifier, en rouge en cas d'échec.",
            "À la fin, un bilan regroupe les problèmes. *Open results* ouvre le dossier `outlined_result`, créé à "
            "côté des photos.",
            "Parcourir le dossier `to_control` (aperçus), puis ouvrir *Review…* pour corriger ce qui doit l'être."]),
    ("p", "Compter 3 à 4 secondes par photo ; plusieurs photos sont traitées en même temps."),

    ("h2", "5. Ce qui sort"),
    ("p", "Tous les fichiers d'une photo gardent son nom, pour se suivre dans l'Explorateur :"),
    ("table", [["Fichier", "Contenu"],
               ["`NOM.JPG`", "Copie de la photo originale (avec les métadonnées IPTC ajoutées, sans recompression)."],
               ["`NOM.psd`", "Photoshop à calques : *Original photo* (masqué, la photo entière), *Scale*, *Ceramic*, "
                             "avec des masques de fusion modifiables au pinceau (blanc = montrer, noir = cacher)."],
               ["`NOM_outlined.tif`", "L'objet seul, fond transparent, à la résolution 1:1."],
               ["`NOM_outlined_scale.tif`", "L'objet et son échelle redressée dessous, fond transparent."],
               ["`to_control/NOM_to_control.jpg`", "L'aperçu de contrôle."],
               ["`outlined_report.csv`", "Le rapport : une ligne par photo, s'ouvre dans Excel."]]),
    ("figure", "fig_control", "L'aperçu de contrôle : contour du détourage en vert, échelle en magenta, "
                              "centimètres trouvés en orange, et la mesure écrite en haut."),
    ("p", "Couleurs de l'aperçu de contrôle :"),
    ("table", [["Couleur", "Signification"],
               ["Vert", "Contour du détourage."],
               ["Magenta", "Cadre de l'échelle trouvée."],
               ["Orange", "Centimètres lus sur l'échelle."],
               ["Rouge", "Ce qui a été écarté (étiquette, charte, petit élément isolé), ou zone de pâte à fixe "
                         "possible."],
               ["Bleu", "Support en plexiglas retiré."],
               ["Cyan", "Fond retiré par le second avis de l'IA."]]),
    ("h3", "Le suffixe _to_be_verified"),
    ("p", "Quand quelque chose est douteux, tous les fichiers écrits pour la photo reçoivent ce suffixe "
          "(par exemple `NOM_outlined_to_be_verified.tif`) : taper `to_be_verified` dans la recherche de "
          "l'Explorateur pour les retrouver. Il y a doute quand :"),
    ("ul", ["l'échelle n'est pas trouvée ;",
            "elle ne mesure pas 5, 10 ou 20 cm, ou ses cases / graduations sont irrégulières ou en partie cachées ;",
            "une zone ressemble à de la pâte à fixe ;",
            "une charte couleur touche l'objet ;",
            "l'objet touche le bord de la photo ;",
            "une information obligatoire manque, ou le nom ne suit pas la règle de nommage."]),
    ("p", "Retraiter un dossier remplace les fichiers des photos retraitées ; le suffixe disparaît si le doute "
          "est levé. La copie de la photo originale garde toujours son nom exact."),

    ("h2", "6. Le rapport outlined_report.csv"),
    ("p", "Une ligne par photo, séparateur « ; » et virgule décimale (Excel français). États : `ok`, `to verify`, "
          "`failed` (aucun objet trouvé), `error`. Colonnes principales :"),
    ("table", [["Colonne", "Contenu"],
               ["`file`, `output_name`", "Nom de la photo, nom des fichiers produits (renommage en lot)."],
               ["`status`, `to_verify`", "État, et raisons du doute."],
               ["`scale_found`, `scale_type`", "Échelle trouvée ? Sa nature : `checkerboard` (damier), `ruler` "
                                               "(réglet), `manual` (à la main), `learned` (apprise)."],
               ["`squares`, `scale_length_cm`", "Nombre de cases, longueur de l'échelle."],
               ["`px_per_cm`, `ppi_1_1`", "La mesure : pixels par centimètre, et la résolution 1:1 qui en découle."],
               ["`ceramic_width_cm`, `ceramic_height_cm`", "Dimensions de l'objet détouré, en cm."],
               ["`pieces`", "Nombre de morceaux détourés."],
               ["`camera`, `lens`, `focal_mm`, `date_taken`", "Informations de prise de vue (EXIF)."],
               ["`notes`, `duration_s`", "Remarques du traitement, durée."]]),
    ("p", "Les champs du renommage en lot (site, US, numéro…) s'ajoutent en colonnes après celles-ci."),

    ("h2", "7. Vérifier et corriger : Review…"),
    ("p", "La fenêtre de vérification montre les photos une par une, **les douteuses et les échecs d'abord**, avec "
          "le contour du détourage (vert, fond assombri) et celui de l'échelle (magenta)."),
    ("table", [["Outil", "Usage"],
               ["*One click on the object (more precise)*", "Cliquer sur chaque objet à garder : Segment Anything "
                    "le détoure (Maj + clic en retire un). Plus fiable sur les photos difficiles, parce qu'on "
                    "**indique au programme quel objet détourer** au lieu de le laisser deviner ce qui est un "
                    "tesson, une étiquette, une ombre ou le fond."],
               ["*Erase* / *Add*", "Pinceau (taille réglable) ou lasso (entourer une zone) pour retirer ou ajouter."],
               ["*Remove a piece*", "Un clic retire un morceau entier (ombre, tache de fond)."],
               ["*Undo* (Ctrl+Z), *Reset photo*", "Annuler la dernière action, ou toutes celles de la photo."],
               ["Orientation", "Tracer un trait le long du bord (lèvre) : il devient horizontal, l'objet dessous. Ou "
                               "tourner par quarts de tour."],
               ["*Fix the scale…*", "Ouvre l'échelle manuelle de la photo."],
               ["*Accept and next*", "Enregistre les corrections et **réexporte la photo aussitôt**, en "
                                     "arrière-plan (« exporting… », puis « ✓ exported »)."]]),
    ("p", "Navigation : molette pour zoomer, barres de défilement, bouton droit ou du milieu, Espace + glisser ou "
          "flèches du clavier pour déplacer la vue ; R pour revoir la photo entière."),
    ("note", "Les corrections sont enregistrées **à côté des photos**, dans un dossier `gerbil_edits` : tous les "
             "traitements suivants les gardent. Rouverte plus tard, la fenêtre montre les corrections déjà faites. "
             "Garder ce dossier avec les photos."),

    ("h2", "8. Donner l'échelle à la main : Set scale…"),
    ("p", "Quand l'échelle d'une photo n'est pas trouvée ou mal lue : sélectionner la photo, *Set scale…*, cliquer "
          "les deux extrémités d'une longueur connue (par exemple 0 et 5 cm, au milieu de l'échelle), donner "
          "cette longueur et la largeur de l'échelle, puis *Save*. La photo peut être retraitée tout de suite."),
    ("p", "L'échelle est gardée dans `gerbil_scales.json`, dans le dossier des photos ; elle l'emporte sur la "
          "recherche automatique à chaque traitement (rapport : `scale_type` = `manual`). À la fin d'un "
          "traitement, Gerbil propose de régler à la suite toutes les échelles qu'il n'a pas trouvées "
          "(*Save and next*, *Skip this photo*, *Stop*)."),

    ("h2", "9. Renommage en lot et informations des photos"),
    ("p", "*Batch renaming…* associe à un dossier de photos des **champs** (par défaut *Site*, *Sector*, *US*, "
          "*Object number*, *Material*, *View*), un **modèle de nom** et une **règle de nommage**. Tout est "
          "enregistré dans `gerbil_project.json`, à côté des photos."),
    ("ul", ["**Modèle de nom**, par exemple `{site}_{sector}_US{us}_{number}_{material}` : les fichiers produits "
            "prennent ce nom (`QSR25_A5_US7549_187_metal_outlined.tif`). **Les photos originales ne sont jamais "
            "renommées.**",
            "**Valeurs** : celles communes à toutes les photos (le site), et un tableau d'une ligne par photo. "
            "Comme dans Excel : double-clic pour modifier, **poignée** au coin d'une case pour recopier vers le "
            "bas (avec Ctrl : une série 187, 188, 189…), Ctrl+D, *Set for selected…*, *Number the selected…*.",
            "**Import CSV / Excel** : un inventaire dont la première ligne porte les noms de colonnes ; la colonne "
            "des noms de photos est trouvée toute seule.",
            "**Règle de nommage** (facultative) : une expression régulière lue comme le `-match` de PowerShell. "
            "L'assistant l'écrit à partir de cases à cocher (majuscules seulement, se termine par un nombre…) et "
            "montre la ligne PowerShell équivalente, pour apprendre."]),
    ("p", "Les informations vont dans le rapport (une colonne par champ) et **dans les fichiers PSD et TIFF** "
          "(XMP : titre = nom de sortie, mots-clés = valeurs)."),

    ("h2", "10. Métadonnées IPTC"),
    ("p", "Dans *Batch renaming*, *IPTC metadata…* remplit les champs IPTC standard (lus par Bridge, Lightroom, "
          "darktable, l'Explorateur Windows) : pour chaque champ (titre, description, mots-clés, auteur, "
          "copyright, lieu…), un texte où `{champ}` est remplacé par la valeur de la photo et `{name}` par le nom "
          "de sortie. Un texte sans accolades est le même pour toutes les photos (copyright, auteur)."),
    ("p", "Ils sont écrits dans les PSD et TIFF, dans la copie de l'original (JPEG : sans recompresser l'image) "
          "et, si coché, dans un fichier `NOM.xmp` à côté de chaque photo originale. Les photos elles-mêmes ne "
          "sont jamais modifiées, et un `.xmp` écrit par un autre logiciel n'est jamais remplacé."),

    ("h2", "11. Profils de site et échelles apprises"),
    ("p", "Un **profil de site** rassemble ce que l'on sait des photos d'un site ou d'une campagne, choisi une fois "
          "sous *SITE PROFILE* (*New…*, *Edit…*) :"),
    ("ul", ["le **fond** : trouvé par Gerbil, clair, ou sombre (velours, feutre) ;",
            "les **échelles apprises** : *Learn a scale from a photo…*, cliquer les deux extrémités de l'échelle et "
            "donner la largeur de sa bande imprimée. Gerbil garde son image et la retrouve sur les autres photos. "
            "Apprendre **chaque exemplaire** utilisé : deux impressions du même modèle peuvent différer de 1 % ;",
            "les **options** de la fenêtre principale (*Keep the options of the main window*)."]),
    ("p", "Par défaut, une échelle apprise est une seconde chance, utilisée quand la lecture habituelle échoue ou "
          "doute ; *Look for the learned scales first* l'utilise en premier. *Put next to the photos…* copie le "
          "profil en `gerbil_profile.json` dans un dossier de photos : il s'applique alors à ces photos, pour "
          "toute l'équipe."),

    ("h2", "12. Les planches : Plates…"),
    ("p", "*Plates…* met en page les objets détourés d'un dossier de résultats à une échelle choisie (1:1, 1:2, "
          "1:3…) et les écrit en **SVG** (dossier `plates`), qui s'ouvrent dans Illustrator ou Inkscape à leur "
          "vraie taille : 1 cm de l'objet = 1 cm ÷ échelle sur le papier."),
    ("ul", ["Objets en **rangées**, dans l'ordre choisi (nom, US, matière…), avec une **légende** sous chacun "
            "(`{name}`, ou `{site}_{us}_{number}`…). *Group by* commence une rangée ou une page à chaque valeur.",
            "**Barre d'échelle** graphique réglée comme dans QGIS (style, longueur, segments, couleurs, police), "
            "gardée comme « style maison ».",
            "**Une échelle par planche** ; un objet trop grand passe au 1:1,5, 1:2, 1:3… sur ses propres planches. "
            "*Scale per object…* ou un clic droit sur un objet de l'aperçu choisit son échelle.",
            "**Échelle par matière** : céramique et verre au 1/3, fer aux 2/3, pierre au 1/3 par défaut (règles "
            "modifiables `mot=réduction`).",
            "**Dessins à côté des photos** : un dossier de dessins (`.svg`, ou `.ai` `.pdf` `.eps` convertis par "
            "Inkscape) ; un dessin nommé comme l'objet est placé à côté de sa photo, à la même échelle, **en "
            "vectoriel** (modifiable dans Illustrator).",
            "**Titre** et **noms de fichiers** à partir de modèles (`{page}`, `{pages}`, `{group}`, `{scale}`).",
            "**Cotes** en option sur un calque masqué : des repères de mise en page, pas des données."]),
    ("p", "L'aperçu montre les pages telles qu'elles seront écrites ; la molette zoome, ◀ ▶ tourne les pages."),

    ("h2", "13. Inventaire et vignettes : menu Tools"),
    ("ul", ["*Inventory (CSV)…* : une ligne par fichier des dossiers choisis (photos, dessins, modèles 3D), avec "
            "dossier, type, taille, date, **les champs lus dans le nom** (même modèle que le renommage), et pour "
            "les images leur taille, résolution, date de prise de vue et appareil. La fenêtre montre la **ligne "
            "PowerShell** qui fait le même inventaire avec Windows seul, à copier pour apprendre.",
            "*Thumbnails…* : copies réduites pour les bases de données (128 à 1 024 px), PNG transparent ou JPEG "
            "sur blanc, marge transparente coupée."]),

    ("h2", "14. Les options"),
    ("p", "Les mêmes options existent dans l'interface et en ligne de commande (`py gerbil.py DOSSIER --option`, ou "
          "`gerbil_cli.exe DOSSIER --option` dans la version .exe) :"),
    ("table", [["Option", "Effet"],
               ["`--background white`", "TIFF sur fond blanc au lieu de transparent."],
               ["`--remove-putty`", "Retire la pâte à fixe trouvée (sinon elle est seulement signalée)."],
               ["`--layout original`", "Laisse l'échelle là où elle est sur la photo, au lieu de la centrer sous "
                                       "l'objet."],
               ["`--scale-cm 10`", "Impose la longueur de l'échelle."],
               ["`--margin-cm 0.5`, `--gap-cm 0.5`", "Marge autour de l'objet, écart entre objet et échelle."],
               ["`--no-original-layer`", "PSD 2 à 4 fois plus léger (sans le calque de la photo entière)."],
               ["`--no-original-copy`", "Ne copie pas la photo originale dans les résultats."],
               ["`--no-psd`, `--no-control`", "Pas de PSD ; pas d'aperçus de contrôle."],
               ["`--compression zip`", "TIFF un peu plus petits (LZW par défaut, le plus compatible)."],
               ["`--default-ppi 300`", "Résolution utilisée quand il n'y a pas d'échelle."],
               ["`--no-scale`", "Ne cherche pas d'échelle."],
               ["`--ai`, `--ai-model birefnet`, `--ai-device cpu`", "Second avis de l'IA (il ne peut que retirer du "
                    "fond) ; modèle plus précis mais plus lent ; forcer le processeur."],
               ["`--profile FICHIER`", "Profil de site à utiliser."],
               ["`-o DOSSIER`, `--open`, `-j 4`, `-v`", "Dossier de sortie ; ouvrir les résultats à la fin ; nombre "
                    "de photos en parallèle ; détail des erreurs."]]),

    ("h2", "15. Les fichiers que Gerbil écrit à côté des photos"),
    ("p", "Ce que l'on décide est enregistré **à côté des photos**, dans de petits fichiers, pour qu'un traitement "
          "suivant ou un collègue les retrouve. À archiver avec les photos :"),
    ("table", [["Fichier", "Contenu"],
               ["`gerbil_project.json`", "Renommage en lot : champs, modèle, règle, valeurs, réglages IPTC."],
               ["`gerbil_scales.json`", "Échelles données à la main."],
               ["`gerbil_edits/`", "Corrections de la fenêtre de vérification (masques corrigés, angles)."],
               ["`gerbil_profile.json`", "Profil de site posé dans le dossier."],
               ["`NOM.xmp`", "Métadonnées IPTC à côté de la photo, si demandé."]]),

    ("h2", "16. Limites"),
    ("ul", ["La mesure n'est juste que si l'échelle est **dans le plan de l'objet**.",
            "Le fond doit être uni et différent de l'objet. Un support opaque blanc ou crème logé dans un creux "
            "n'est pas reconnu : l'effacer dans *Review…* ou dans Photoshop.",
            "Une autre forme d'échelle sera le plus souvent signalée à vérifier : l'apprendre dans un profil de "
            "site, ou la donner à la main.",
            "Pour un rendu des couleurs précis des RAW, les développer soi-même (Lightroom, darktable) et donner "
            "les TIFF à Gerbil."]),

    # =========================================================================================== PARTIE II
    ("pagebreak",),
    ("h1", "Partie II — Comprendre les traitements"),
    ("p", "Cette partie explique ce que fait Gerbil, étape par étape, sans programmation. Les seuils donnés sont "
          "ceux du code ; le document `docs/PSEUDOCODE.txt` les détaille tous."),

    ("h2", "1. Le chemin d'une photo"),
    ("ol", ["**Lecture** : la photo est ouverte et redressée (orientation EXIF) ; un RAW est développé.",
            "**Copie réduite** à 1 500 px pour l'analyse : plus rapide, et suffisant pour trouver les choses ; les "
            "mesures fines sont refaites à pleine résolution.",
            "**Modèle du fond** : la couleur du fond en tout point de la photo.",
            "**Échelle** : manuelle si on l'a donnée, sinon cherchée (damier, réglet, fond sombre), sinon une "
            "échelle apprise du profil de site.",
            "**Détourage** : ce qui diffère du fond, trié, affiné à pleine résolution.",
            "**Pâte à fixe** cherchée sur le contour.",
            "**Fichiers** : calques, PSD, TIFF à la résolution 1:1, métadonnées, aperçu, ligne du rapport."]),

    ("h2", "2. Voir les couleurs comme l'œil : CIELAB"),
    ("p", "Une photo est faite de pixels rouge, vert, bleu (RVB). Mais en RVB, deux couleurs « également "
          "différentes » pour l'œil peuvent avoir des écarts de chiffres très différents. Gerbil travaille donc en "
          "**CIELAB** : **L\\*** est la clarté (0 = noir, 100 = blanc), **a\\*** va du vert au rouge, **b\\*** du "
          "bleu au jaune. Dans cet espace, une distance entre deux couleurs correspond à peu près à ce que l'on "
          "perçoit, ce qui permet de dire en chiffres qu'un pixel est « différent du fond »."),
    ("p", "La distance d'un pixel au fond est calculée ainsi :"),
    ("code", "d = racine( (0,5 × ΔL*)² + Δa*² + Δb*² )"),
    ("p", "La clarté ne compte que pour moitié : une **ombre douce** change surtout la clarté du fond, pas sa "
          "couleur ; ainsi elle reste hors de l'objet. Le **chroma** C\\* = racine(a\\*² + b\\*²) dit si une "
          "couleur est vive ou grise ; la **teinte** h est son angle (rouge, jaune, vert, bleu)."),

    ("h2", "3. Le modèle du fond"),
    ("p", "Le fond n'est jamais parfaitement uniforme : l'éclairage fait un dégradé. Gerbil ne prend donc pas une "
          "seule couleur de fond, mais une **surface** qui suit ce dégradé : pour chacun des canaux L\\*, a\\* et "
          "b\\*, un polynôme de degré 2 en x et y (une sorte de « nappe » légèrement courbée), ajusté par **moindres "
          "carrés** sur les pixels du fond."),
    ("ol", ["Départ : la couleur médiane de la photo (le fond est la plus grande partie). Si l'objet remplit le "
            "cadre, on prend plutôt la médiane d'une bande de 3 % le long des bords.",
            "Les pixels proches de cette couleur (distance < 12) sont le premier fond.",
            "Quatre fois : on ajuste la nappe sur ces pixels, puis on ne garde comme fond que ceux qui en sont "
            "très proches (distance < 6). L'objet et l'échelle, trop différents, sont écartés de l'ajustement."]),
    ("p", "Si la clarté médiane du fond est inférieure à 35, le fond est déclaré **sombre** (velours, feutre) : "
          "plusieurs règles changent alors (étiquettes, bords, échelle)."),

    ("h2", "4. Trouver l'objet"),
    ("ul", ["**Distance au fond** de chaque pixel, avec la nappe du fond.",
            "**Seuillage par hystérésis** (seuils 8 et 18) : on garde les régions plus différentes que 8 qui "
            "contiennent au moins un pixel plus différent que 18. Un bord pâle est ainsi gardé s'il appartient à "
            "un objet net, mais une tache pâle isolée ne l'est pas (le principe du détecteur de contours de "
            "Canny, appliqué aux régions).",
            "**Morphologie mathématique** : une *ouverture* (rétrécir puis regrossir) efface les poussières et les "
            "fils fins ; une *fermeture* (grossir puis rétrécir) bouche les petites brèches.",
            "**Trous** : un trou dont la couleur moyenne est celle du fond et d'au moins 0,02 cm² est une vraie "
            "ouverture (anse, perforation) et reste transparent ; les autres (reflet de glaçure, concrétion "
            "claire) sont bouchés."]),

    ("h2", "5. Faire le tri"),
    ("p", "Tout ce qui diffère du fond n'est pas l'objet. Les morceaux trouvés sont triés :"),
    ("table", [["Élément", "Comment il est reconnu"],
               ["L'échelle", "Sa zone (élargie pour son support ou sa pâte) est retirée ; un objet posé tout près "
                             "est gardé s'il s'en éloigne d'au moins 8 mm et diffère nettement du fond."],
               ["Échelle, réglet, étiquette sans échelle mesurée", "Quand l'échelle n'est pas mesurée (non "
                    "trouvée, d'un autre modèle, ou option `--no-scale`), elle reste hors du détourage : son contour "
                    "est fait de longs côtés droits à angle droit (même une barre en L, ou un réglet dont les "
                    "graduations font un peigne), et son contenu est celui d'un imprimé (noir et blanc, peu "
                    "coloré, ou rectangle plein). Sur 191 photos libres, aucun objet écarté ainsi : une épingle, "
                    "une lame noire ou un os allongé restent des objets."],
               ["Ombre portée (fond clair)", "Plus sombre que le fond mais de sa couleur, lisse, le long du contour, "
                    "et elle se fond dans le fond : son bord extérieur est flou (pénombre), alors que le bord "
                    "d'un objet est net. Une partie sombre et lisse de l'objet (vernis noir, obsidienne, silex "
                    "gris) ne touche pas le fond ainsi et reste. Contour bleu sur l'aperçu."],
               ["Support en plexiglas", "Couleur presque celle du fond (distance < 15), dépasse de l'objet, aussi "
                                        "clair ou plus blanc que le fond. Un reflet sur une glaçure noire, plus "
                                        "sombre et le long de l'objet, est laissé."],
               ["Charte couleur", "Beaucoup de teintes vives différentes : au moins 5 secteurs de teinte sur 12, "
                                  "dont un chaud, un vert et un bleu. Une céramique, même peinte, en couvre 2 au "
                                  "plus (1 763 photos testées) ; les chartes 5 à 9."],
               ["Étiquettes, écritures", "Ce qui est de l'autre côté de l'échelle ; ce qui est partout plus fin que "
                                         "1,7 mm (écriture, fil, ligne de sachet) ; les petits éléments isolés à "
                                         "plus de 8 mm de l'objet (sur fond clair)."],
               ["Étiquette papier (fond sombre)", "Claire et rectangulaire (elle remplit 85 % de son rectangle) : "
                    "blanche, blanc bleuté (azurants optiques du papier) ou jaune pâle ; ou très rectangulaire "
                    "(95 %) et claire, quelle que soit sa couleur — un tesson cassé ne remplit jamais autant son "
                    "rectangle."]]),
    ("p", "Une étiquette qui touche un tesson par un coin est découpée à la jonction étroite. Si le seul objet "
          "d'une photo ressemble à une étiquette (petit tesson pâle et carré), il est gardé et la photo signalée."),
    ("figure", "fig_dark", "Sur feutre sombre : l'étiquette papier est reconnue et écartée (contour rouge), le "
                           "tesson est gardé (contour vert)."),

    ("h2", "6. Affiner et adoucir le bord"),
    ("p", "Le premier détourage est fait sur la copie réduite ; il est refait **à pleine résolution** dans une "
          "bande autour de son contour. Une partie est « sûre » (bien à l'intérieur et différente du fond), une "
          "autre « permise » (près du contour) : le bord final est cherché dans la bande, pixel par pixel. Le "
          "masque est ensuite adouci (flou gaussien de 0,8 px) : un bord net mais sans escalier, comme un "
          "détourage fait à la main."),
    ("p", "Sur fond sombre, le bord d'un objet clair est un dégradé de plusieurs pixels (léger flou, ombre). Le "
          "bord est placé **au milieu de ce dégradé**, puis la couleur des derniers pixels du bord est remplacée "
          "par celle de l'objet juste à l'intérieur, sans déplacer le contour : il ne reste pas de liseré sombre."),

    ("h2", "7. Lire une échelle à damier"),
    ("ol", ["**Repérer** l'encre : pixels noirs et rouges vifs, reliés en groupes allongés (une échelle est au moins "
            "2,5 fois plus longue que large).",
            "**Redresser** : une vignette est extraite et tournée pour que l'échelle soit horizontale.",
            "**Lire les cases** : colonne par colonne, quelle rangée est encrée (haut, bas, les deux, aucune) ; les "
            "suites de colonnes semblables sont les cases. Les suites trop courtes (chiffres, flèches) sont "
            "absorbées par leurs voisines.",
            "**Seconde lecture** si des chiffres sont imprimés dans les cases (« 5 », « 10 », « cm ») : on cherche "
            "les **limites** entre cases (là où l'encre passe d'une rangée à l'autre), et on y ajuste un « peigne » "
            "régulier sur toute la longueur.",
            "**Mesurer à pleine résolution** : px/cm = longueur des cases ÷ nombre de cases (une case = 1 cm), au "
            "sous-pixel (là où le profil croise la moitié du contraste).",
            "**Mettre à l'endroit** : les signes imprimés (« 5 », « 10 », « cm ») sont comparés à des modèles de "
            "chiffres dessinés avec 12 polices courantes, à l'endroit et retournés. Sur 1 265 échelles "
            "d'orientation connue : aucune erreur."]),
    ("p", "Vérifications : longueur habituelle (5, 10 ou 20 cm), cases régulières (écart < 15 %). Une échelle coupée "
          "par le bord de la photo est mesurée sur ses cases complètes. Sur fond sombre, les cases noires se "
          "confondent avec le fond : l'échelle est cherchée par ses cases claires, puis tout ce qui l'entoure est "
          "peint en blanc pour la lire comme sur fond clair."),

    ("h2", "8. Lire un réglet millimétré"),
    ("p", "Les graduations sont des traits sombres fins et parallèles. Gerbil les repère (filtre « black-hat », qui "
          "fait ressortir les petits détails sombres), les regroupe en rangées régulières, puis ajuste une suite "
          "régulière x = début + pas × k sur la cinquantaine de graduations. Mesurer un pas sur ~50 intervalles "
          "donne une précision d'environ **0,1 %**. Les graduations du centimètre, plus longues, donnent la "
          "longueur (5 ou 10 cm)."),

    ("h2", "9. Les échelles apprises"),
    ("p", "Pour une échelle d'une autre forme, on montre une fois ses deux extrémités : Gerbil garde son image "
          "redressée. Sur une autre photo, il la cherche en deux temps :"),
    ("ul", ["**Grossièrement** : des points caractéristiques (méthode SIFT : coins, détails reconnaissables même "
            "tournés ou à une autre taille) sont appariés entre l'image apprise et la photo ; une position, une "
            "taille et un angle communs sont trouvés par **RANSAC** (on essaie de nombreux petits groupes de "
            "points et on garde l'explication sur laquelle le plus de points s'accordent).",
            "**Finement** : l'image apprise est alignée sur la photo par corrélation (méthode ECC), ce qui mesure "
            "la longueur à mieux que 0,1 % quand c'est la même échelle physique (0,05 % mesuré)."]),

    ("h2", "10. La pâte à fixe"),
    ("p", "Gerbil cherche sur le contour deux creux (concavités) qui découpent une partie de l'objet. Cette partie "
          "est de la pâte possible si elle est à la fois **plus lisse** (texture moitié moindre), **d'une autre "
          "couleur**, **moins colorée** et **plus claire** que le reste. Par défaut elle est seulement signalée "
          "(zone rouge) : un fond de vase clair et lisse lui ressemble trop pour être retiré sans contrôle."),

    ("h2", "11. Le second avis de l'IA (option)"),
    ("p", "Avec `--ai`, un réseau de neurones de détourage (IS-Net ou BiRefNet) donne son avis. Il ne peut **que "
          "retirer** du fond, jamais ajouter : une zone n'est retirée que si le détourage la garde, que l'IA y "
          "voit du fond, que sa couleur reste proche du fond et qu'elle fait au moins 0,02 cm². Cela ouvre les "
          "perforations dans l'ombre, les écarts entre deux tessons, les halos le long d'un bord flou. Quand l'IA "
          "se trompe, c'est en gardant trop (étiquette, support) : ses erreurs n'ont donc pas d'effet."),

    ("h2", "12. Le détourage en un clic"),
    ("p", "Dans la vérification, l'outil « un clic » utilise **Segment Anything** (version MobileSAM, hors ligne, "
          "45 Mo) : on clique sur l'objet, il le détoure. Il est plus fiable sur les photos difficiles parce qu'on "
          "lui **dit quel objet** détourer : il n'a plus à deviner ce qui est un tesson, une étiquette, une ombre "
          "ou le fond. Son bord étant moins précis, Gerbil garde le bord de son propre détourage là où les deux "
          "sont d'accord."),

    ("h2", "13. De la mesure au 1:1"),
    ("p", "Un fichier image porte une **résolution** : le nombre de pixels par pouce (ppp, ou ppi). Illustrator s'en "
          "sert pour donner sa taille à une image placée. Gerbil inscrit donc dans chaque fichier la résolution "
          "mesurée sur l'échelle :"),
    ("code", "ppi = px/cm × 2,54        (1 pouce = 2,54 cm)\nexemple : 100 px/cm → 254 ppi : un tesson de 600 px de large mesure 6 cm"),
    ("p", "Glissé dans Illustrator, l'objet a donc sa taille réelle. L'échelle de `NOM_outlined_scale.tif` mesure "
          "exactement 5 ou 10 cm avec la règle d'Illustrator : c'est le contrôle le plus simple. L'image n'est "
          "jamais agrandie ni réduite ; seule l'étiquette de résolution change."),
    ("p", "Le **PSD** est écrit octet par octet : le calque *Ceramic* contient les pixels d'origine et un **masque "
          "de fusion** (rien n'est effacé : un coup de pinceau blanc ramène ce qui a été caché) ; *Scale* contient "
          "l'échelle redressée ; *Original photo*, masqué, la photo entière, alignée sur l'objet. Les **TIFF** "
          "sont sans perte (LZW), avec transparence ; un JPEG, lui, recompresserait l'image à chaque "
          "enregistrement."),

    ("h2", "14. Les métadonnées"),
    ("ul", ["**EXIF** : les informations de l'appareil (boîtier, objectif, focale, date, ouverture, vitesse, ISO), "
            "recopiées et mises à jour.",
            "**XMP** : un paquet de texte structuré, inscrit dans les fichiers : la mesure de l'échelle, le nom de "
            "sortie, les champs du renommage.",
            "**IPTC Core** : les champs standard des photothèques (titre, mots-clés, auteur, copyright, lieu), "
            "écrits dans le XMP selon le modèle du projet. Dans un JPEG, le segment XMP est ajouté sans toucher "
            "aux données de l'image (vérifié pixel pour pixel par les tests)."]),

    ("h2", "15. Les planches : du réel au papier"),
    ("p", "Chaque objet a sa taille réelle, lue dans la résolution de son TIFF. À l'échelle 1:r, sa taille sur le "
          "papier est : taille réelle ÷ r. Exemple : un tesson de 6 cm au 1:2 fait 3 cm sur la planche. La page "
          "est d'abord décrite comme une liste de formes **en millimètres** (rectangles, textes, images, dessins) ; "
          "cette même description est écrite en SVG et dessinée pour l'aperçu, qui montre donc exactement ce qui "
          "sera écrit."),

    ("h2", "16. Pour une méthodologie"),
    ("p", "Exemple de paragraphe, à adapter :"),
    ("note", "« Les objets ont été photographiés sur fond uni avec une échelle dans le plan de la face photographiée. "
             "Les photographies ont été détourées et mises à l'échelle avec Gerbil 2.0 (Charbonnel 2026, logiciel "
             "libre, GPL v3). L'échelle de chaque photographie est détectée et mesurée automatiquement (damier : "
             "longueur des cases ajustée au sous-pixel ; réglet : pas du millimètre ajusté sur l'ensemble des "
             "graduations, précision d'environ 0,1 %), puis la résolution réelle est inscrite dans les fichiers, ce "
             "qui restitue les objets au 1:1. Le détourage repose sur la distance de couleur (CIELAB) à un modèle "
             "polynomial du fond, avec seuillage par hystérésis ; les cas douteux ont été signalés par le logiciel "
             "et vérifiés un à un. »"),

    # =========================================================================================== PARTIE III
    ("pagebreak",),
    ("h1", "Partie III — Lire le code"),

    ("h2", "1. Les fichiers"),
    ("table", [["Fichier", "Rôle"],
               ["`gerbil.py`", "Le moteur : tout ce qui traite une photo, et la ligne de commande. Il ne sait rien "
                               "des fenêtres."],
               ["`gerbil_gui.pyw`", "L'interface : les fenêtres. Elle lance le moteur comme un programme séparé et "
                                    "lit ce qu'il affiche."],
               ["`gerbil_plates.py`", "Les planches SVG."],
               ["`gerbil_tools.py`", "L'inventaire CSV et les vignettes."],
               ["`packaging/gerbil_setup.pyw`", "L'installateur."],
               ["`tests/`", "Les tests automatiques, sur des photos synthétiques."],
               ["`docs/`", "Pseudo-code, feuille de route, sources, ce guide."]]),

    ("h2", "2. Comment ils se parlent"),
    ("code", "gerbil_gui.pyw  (fenêtres)  --lance-->  gerbil.py / gerbil_cli.exe  (moteur, photo après photo)\n"
             "       |                                   |\n"
             "       |  lit les lignes affichées         +--> outlined_result/ : PSD, TIFF, aperçus, rapport\n"
             "       |  (« [3/12] NOM: ok ... »)         |\n"
             "       +--> gerbil_plates.py (planches)    +--> lit gerbil_project.json, gerbil_scales.json,\n"
             "       +--> gerbil_tools.py  (inventaire)       gerbil_edits/, gerbil_profile.json"),
    ("p", "L'interface ne traite pas les photos elle-même : elle construit la ligne de commande à partir des "
          "options, lance le moteur (`subprocess`), et lit les lignes qu'il affiche pour montrer l'avancement. "
          "Quelques fenêtres appellent aussi directement des fonctions du moteur (`import gerbil`), par exemple "
          "pour lire une photo ou apprendre une échelle."),

    ("h2", "3. Le chemin d'une photo dans le code"),
    ("p", "La fonction `process_photo` de `gerbil.py` appelle, dans l'ordre :"),
    ("ol", ["`load_photo` : lit le fichier (RAW par `develop_raw`), le redresse, garde EXIF et profil couleur.",
            "`BackgroundModel` : le modèle du fond, sur la copie réduite.",
            "`manual_scale`, sinon `detect_scale` (qui appelle `analyze_pattern`, `analyze_comb`, `detect_ruler`, "
            "`_scale_on_dark`…), sinon `detect_learned_scale`. Le résultat est un objet `Scale`.",
            "`outline_ceramic` (ou `cutout_from_mask` pour un masque corrigé à la main).",
            "`find_putty`.",
            "`layout`, puis `write_psd`, `write_tiff` (avec `make_xmp`), `control_image`, `write_review`.",
            "La ligne du rapport est renvoyée ; `main` écrit `outlined_report.csv` et le bilan."]),

    ("h2", "4. Les notions de Python utiles"),
    ("defs", [("Module, import", "Chaque fichier est un module. `import gerbil as g` donne accès à ses fonctions "
                                 "(`g.load_photo`) ; `from PIL import Image` prend un seul nom dans une "
                                 "bibliothèque."),
              ("Fonction", "`def nom(arguments):` reçoit des valeurs et renvoie un résultat (`return`). Le corps de "
                           "la fonction est le bloc décalé (indenté) sous la ligne `def`."),
              ("Docstring", "La première chaîne d'une fonction, entre triples guillemets : son explication. C'est "
                            "elle, traduite, que montre la partie IV."),
              ("Classe, méthode, self", "`class Nom:` regroupe des données et les fonctions qui travaillent dessus "
                    "(ses *méthodes*). Le premier argument d'une méthode, `self`, est l'objet lui-même. Chaque "
                    "fenêtre est une classe (`ReviewWindow`, `PlatesWindow`) : son `__init__` la construit, ses "
                    "méthodes réagissent à l'utilisateur."),
              ("@dataclass", "Une classe qui est surtout une fiche de valeurs nommées (`Scale`, `PlateSettings`), "
                             "écrite sans répétitions."),
              ("Dictionnaire, liste, tuple", "`{\"clé\": valeur}` : réglages, lignes du rapport, fichiers JSON. "
                    "`[a, b]` : valeurs ordonnées, modifiables. `(x, y)` : groupe fixe (coordonnées, couleurs)."),
              ("Tableau numpy", "Une image est un tableau : `rgb[y, x]` est un pixel, `rgb.shape` vaut (hauteur, "
                    "largeur, 3), valeurs de 0 à 255. Une opération s'applique à tous les pixels d'un coup "
                    "(`rgb * 0.5`), sans boucle : c'est ce qui rend le traitement rapide."),
              ("Masque", "Un tableau de vrai / faux de la taille de l'image : `rgb[masque]` donne les pixels de "
                         "l'objet."),
              ("OpenCV (cv2)", "Le traitement d'image : redimensionner, flouter, convertir en Lab, morphologie "
                    "(`cv2.erode` rétrécit un masque, `cv2.dilate` le grossit), composantes connexes (les morceaux "
                    "séparés d'un masque), contours."),
              ("Pillow (PIL)", "Lire et écrire les fichiers image, dessiner des textes, les profils couleur."),
              ("Coordonnées", "x vers la droite, y vers le bas, en pixels de la photo ; en millimètres de la page "
                    "pour les planches. Une matrice affine `M` (2 × 3) fait passer d'une vignette redressée à la "
                    "photo."),
              ("Exceptions", "`try: … except OSError:` attrape une erreur (un fichier illisible) au lieu d'arrêter "
                             "le programme."),
              ("f-string", "`f\"{px_cm:.2f} px/cm\"` écrit des valeurs dans un texte (ici avec 2 décimales)."),
              ("Travail en parallèle", "Le moteur traite plusieurs photos à la fois dans des processus séparés "
                    "(`ProcessPoolExecutor`). L'interface reste réactive en faisant les longs travaux dans des "
                    "fils d'exécution (`threading.Thread`) et en vérifiant régulièrement avec `after(ms, "
                    "fonction)`."),
              ("tkinter", "Les fenêtres : des éléments (`ttk.Button`, `tk.Canvas`) placés avec `pack` ou `grid` ; "
                          "`command=` et `bind(\"<Événement>\", fonction)` relient un clic ou une touche à une "
                          "méthode ; `mainloop()` attend les événements.")]),

    ("h2", "5. Petit lexique pour lire une ligne"),
    ("table", [["Écrit", "Se lit"],
               ["`a = b`", "a reçoit la valeur de b (ce n'est pas une égalité)."],
               ["`a == b`, `a != b`", "a est-il égal à b ? différent de b ? (vrai ou faux)"],
               ["`a += 1`, `a *= 2`", "a augmente de 1 ; a est multiplié par 2."],
               ["`x ** 2`", "x au carré."],
               ["`if … :`, `elif … :`, `else:`", "si…, sinon si…, sinon."],
               ["`for x in liste:`", "pour chaque élément de la liste."],
               ["`and`, `or`, `not`", "et, ou, non."],
               ["`# texte`", "un commentaire : ignoré par Python, écrit pour le lecteur."],
               ["`lab[..., 0]`", "dans un tableau d'image, le canal 0 (L\\*) de tous les pixels."],
               ["`rgb[y0:y1, x0:x1]`", "un rectangle de l'image (de y0 à y1 exclu, de x0 à x1 exclu)."],
               ["`np.`, `cv2.`", "une fonction de numpy, d'OpenCV."],
               ["`self.nom`", "une donnée de l'objet (la fenêtre, l'échelle…)."],
               ["`None`", "« rien » : pas de valeur (échelle non trouvée, par exemple)."]]),

    ("h2", "6. Des fonctions réelles, ligne par ligne"),
    ("p", "Les extraits suivants sont lus dans le code au moment où ce guide est produit : ce sont exactement les "
          "lignes du programme."),
    ("h3", "to_lab : passer en couleurs CIELAB"),
    ("annotated", "gerbil.py", "to_lab", [
        "Définit la fonction `to_lab`, qui reçoit `rgb`, une image en rouge-vert-bleu.",
        "La docstring : ce que fait la fonction et pourquoi (voir Partie II, § 2).",
        "OpenCV convertit l'image en Lab ; `.astype(np.float32)` passe en nombres à virgule, pour calculer sans "
        "arrondis. OpenCV range chaque canal de 0 à 255.",
        "Le canal 0 (L\\*) est ramené de 0–255 à l'échelle habituelle 0–100.",
        "Les canaux 1 et 2 (a\\* et b\\*) sont recentrés autour de 0 (OpenCV les décale de 128).",
        "Renvoie l'image en Lab."]),
    ("h3", "distance : à quel point un pixel diffère du fond"),
    ("annotated", "gerbil.py", "distance", [
        "Reçoit l'image en Lab, la couleur de référence (le modèle du fond) et le poids de la clarté, par défaut "
        "`L_WEIGHT` (0,5).",
        "La docstring.",
        "Écart de clarté (L\\*) de chaque pixel au fond, multiplié par le poids : une ombre compte moins.",
        "Écart sur a\\* (vert–rouge).",
        "Écart sur b\\* (bleu–jaune).",
        "La distance : racine de la somme des carrés (le théorème de Pythagore dans l'espace des couleurs), pour "
        "tous les pixels à la fois."]),
    ("h3", "hysteresis : garder les régions nettes et leurs bords pâles"),
    ("annotated", "gerbil.py", "hysteresis", [
        "Reçoit la carte des distances `d` et les deux seuils (8 et 18 pour le détourage).",
        "La docstring.",
        "`weak` : les pixels au-dessus du seuil bas (1 = oui, 0 = non).",
        "OpenCV numérote les régions d'un seul tenant de `weak` (`n` régions ; `lab` donne le numéro de chaque "
        "pixel). Ce `lab` n'a rien à voir avec les couleurs Lab : c'est une « étiquette ».",
        "Une liste de `n` réponses « garder ? », toutes à non pour commencer.",
        "Les numéros des régions qui contiennent au moins un pixel au-dessus du seuil haut passent à oui.",
        "La région 0, le fond, n'est jamais gardée.",
        "Chaque pixel prend la réponse de sa région : on obtient le masque."]),
    ("h3", "parse_ratio : lire une échelle écrite « 1/3 »"),
    ("annotated", "gerbil_plates.py", "parse_ratio", [
        "Reçoit un texte, par exemple « 1/3 », « 1:3 » ou « 3 ».",
        "La docstring donne des exemples : « 2/3 » donne 1,5 (réduction aux deux tiers).",
        "Le texte est nettoyé (espaces retirés) ; une virgule décimale devient un point, comme le veut Python.",
        "Essayer ce qui suit ; en cas d'erreur, aller à `except`.",
        "Si le texte contient « / » ou « : »…",
        "… le couper en deux à ce signe : `a` avant, `b` après.",
        "… et renvoyer b ÷ a (1/3 → 3, 2/3 → 1,5).",
        "Sinon, le texte est un nombre seul : le renvoyer.",
        "Si la lecture échoue (pas un nombre) ou divise par zéro…",
        "… renvoyer `None` : l'interface garde alors l'ancienne valeur."]),
    ("h3", "Tooltip.__init__ : relier une bulle d'aide à un bouton"),
    ("annotated", "gerbil_gui.pyw", "Tooltip.__init__", [
        "La méthode qui construit une bulle d'aide : `self` est la bulle, `widget` l'élément (bouton, case), "
        "`text` l'explication.",
        "La docstring.",
        "Garde l'élément et le texte ; la bulle elle-même (`tip`) et la tâche prévue (`job`) n'existent pas "
        "encore.",
        "Quand la souris **entre** sur l'élément : prévoir l'affichage (`_schedule`, dans 450 ms). `add=\"+\"` "
        "ajoute ce lien sans effacer ceux qui existent déjà.",
        "Quand la souris **sort** : cacher la bulle.",
        "Au **clic** : la cacher.",
        "Quand l'élément perd le **focus** (on passe à autre chose) : la cacher.",
        "Quand l'élément est **détruit** (fenêtre fermée) : la cacher."]),

    ("h2", "7. Modifier le code sans rien casser"),
    ("ul", ["Noms et messages en anglais ; les constantes en majuscules en haut de leur section (`LOW_T`, "
            "`LABEL_FILL`…), avec un commentaire qui dit ce qu'elles sont.",
            "Les commentaires disent *pourquoi* quand ce n'est pas évident ; les docstrings disent *quoi* et, "
            "brièvement, *comment*.",
            "**Un changement doit laisser identiques, au pixel près, les résultats déjà justes** : on le vérifie "
            "sur les lots de photos de référence avant de l'adopter (voir `CONTRIBUTING.md`).",
            "Les tests automatiques se lancent avec `py -3 -m pytest tests` ; ils fabriquent leurs propres photos "
            "synthétiques (le dépôt ne contient aucune photo réelle).",
            "Après un changement du code, relancer `py -3 docs/make_guide_odt.py` : ce guide se met à jour. Une "
            "fonction nouvelle sans explication française apparaît avec son explication anglaise, marquée « à "
            "traduire » : l'ajouter dans `docs/fr/reference_fr.py`."]),

    ("h2", "8. Glossaire"),
    ("defs", [("Affine (transformation)", "Rotation, changement de taille et déplacement combinés ; sert à redresser "
                                          "une échelle."),
              ("Alpha, masque de fusion", "La transparence de chaque pixel : 0 = transparent, 255 = opaque. Dans le "
                                          "PSD, le masque cache sans effacer."),
              ("Composante connexe", "Un morceau d'un seul tenant d'un masque."),
              ("ECC", "Méthode d'alignement fin de deux images par corrélation."),
              ("Hystérésis", "Seuillage à deux seuils : garder ce qui dépasse le seuil bas s'il touche ce qui "
                             "dépasse le seuil haut."),
              ("Moindres carrés", "Ajuster une courbe ou une surface pour que la somme des carrés des écarts soit la "
                                  "plus petite possible."),
              ("Morphologie (ouverture, fermeture)", "Opérations sur la forme d'un masque : l'ouverture efface ce qui "
                    "est plus fin qu'un disque donné, la fermeture bouche les brèches plus étroites."),
              ("ONNX, onnxruntime", "Format des réseaux de neurones, et le programme qui les exécute."),
              ("px/cm, ppi", "Pixels par centimètre (mesurés sur l'échelle) ; pixels par pouce (= px/cm × 2,54), "
                             "inscrits dans les fichiers."),
              ("RANSAC", "Méthode robuste : essayer de nombreuses petites explications et garder celle que le plus "
                         "de données confirment."),
              ("SIFT", "Points caractéristiques d'une image, reconnaissables même tournés ou agrandis."),
              ("Sous-pixel", "Position mesurée plus finement que le pixel, en interpolant le profil de clarté."),
              ("SVG", "Format de dessin vectoriel (XML) lu par Illustrator et Inkscape."),
              ("XMP, IPTC, EXIF", "Métadonnées inscrites dans les fichiers : XMP est le format, IPTC le jeu de champs "
                                  "des photothèques, EXIF les informations de l'appareil.")]),
]
