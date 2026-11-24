"""Texte des guides en français, lu par docs/make_guide_pdf.py :

- USER : le guide de l'utilisateur (docs/Gerbil_guide_FR.pdf) ;
- CODE : le guide du code (docs/Gerbil_code_guide_FR.pdf), suivi de la référence des fonctions faite à partir
  du code, avec les explications de reference_fr.py et reference_fr_more.py.

Blocs : ("part", numéro, titre, chapeau, ancre), ("h2"|"h3", titre[, ancre]), ("p", texte), ("lead", texte),
("ul"|"ol", [éléments]), ("code", texte), ("tip"|"warn"|"note"|"key", texte), ("quote", texte),
("table", [en-tête, lignes…][, largeurs]), ("figure", image, légende), ("shot", capture, légende[, "half"]),
("defs", [(terme, définition)…]), ("flow", [(n°, titre, texte, ancre)…]), ("cards", [(question, réponse,
ancre)…]), ("annotated", fichier, fonction, [explication de chaque ligne]), ("pagebreak",).
Dans les textes : **gras**, *italique*, `code`, [[ancre]] ou [[ancre|texte]] (renvoi), {{Ctrl+Z}} (touches),
<https://…> (lien)."""

LABELS = {
    "contents": "Sommaire", "part": "PARTIE", "in_part": "Dans cette partie", "line": "ligne", "lines": "lignes", "function": "fonction",
    "class": "classe", "method": "méthode", "untranslated": "(à traduire)",
    "helper": "(petite fonction utilitaire : voir le code)",
    "tip": "Astuce", "warn": "Attention", "note": "À savoir", "key": "L'essentiel",
    "code_col": "Code", "expl_col": "Ce que fait la ligne",
    "ref_title": "Référence des fonctions",
    "ref_intro": "Chaque fichier du programme, ses sections (les bandeaux « # ---- » du code) et, dans chacune, "
        "toutes ses fonctions et classes, avec leur explication et leur numéro de ligne. Le nom en gras est "
        "celui que l'on cherche dans le code (Ctrl+F) ; entre parenthèses, ce que la fonction reçoit.",
    "generated": "Cette partie est écrite automatiquement à partir du code (docs/make_guide_pdf.py) : elle suit "
        "toujours la version du programme.",
    "version": "Version", "licence": "Logiciel libre, licence GNU GPL v3 ou ultérieure",
    "date": "Guide produit le",
}

USER_META = {
    "subtitle": "Guide de l'utilisateur",
    "tagline": "Des photographies d'objets et de terrain jusqu'aux planches publiées et aux archives : le "
               "parcours complet, étape par étape, avec ses possibilités, ses méthodes et ses sources.",
    "footer": "Gerbil {version}, guide de l'utilisateur",
}
CODE_META = {
    "subtitle": "Guide du code",
    "tagline": "Comment le programme est organisé, les notions de Python pour le lire, des fonctions commentées "
               "ligne par ligne, et la référence de toutes les fonctions.",
    "footer": "Gerbil {version}, guide du code",
    "ref_number": "5",
}

FILE_ROLES = {
    "gerbil.py": "Le moteur et la ligne de commande : tout ce qui traite une photo.",
    "gerbil_gui.pyw": "L'interface (les fenêtres) : elle lance le moteur comme un programme séparé.",
    "gerbil_plates.py": "Les planches : objets mis en page à une échelle choisie, écrits en SVG.",
    "gerbil_tools.py": "L'inventaire (CSV) et les vignettes.",
    "gerbil_dng.py": "La conversion des RAW en DNG, avec leurs métadonnées et leurs nouveaux noms.",
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
    "Object outlining": "Détourage de l'objet",
    "Deposit: check of a folder before it goes to an archive":
        "Versement : contrôle d'un dossier avant sa remise à un service d'archives",
    "Colour: white balance and exposure from a white reference of the photo":
        "Couleur : balance des blancs et exposition d'après un blanc de la photographie",
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

# =============================================================================================================
# GUIDE DE L'UTILISATEUR
# =============================================================================================================

USER = [
    # ------------------------------------------------------------------------------------------------ 1
    ("part", "1", "Bienvenue", "Gerbil est la boîte à outils photographique de l'archéologue : il détoure "
     "les objets à leur taille réelle, nomme et documente les photographies, les convertit pour l'archive et "
     "compose les planches. Ce guide en fait le tour, de la prise de vue au versement.", "bienvenue"),

    ("h2", "Je veux…", "je-veux"),
    ("cards", [
        ("Détourer des objets à leur taille réelle", "étape 03, puis vérifier", "etape-03"),
        ("Nommer mes fichiers d'après l'inventaire", "renommage en lot, import CSV", "etape-02"),
        ("Archiver mes RAW en DNG avec leurs métadonnées", "étape 04", "etape-04"),
        ("Faire des planches au 1/3", "planches à l'échelle", "planches"),
        ("Mettre des sépultures à la même échelle", "planches libres", "planches-libres"),
        ("Préparer un versement aux archives", "revue finale", "etape-05"),
        ("Corriger un détourage", "fenêtre de vérification", "verifier"),
        ("Donner l'échelle à la main", "deux clics et une longueur", "echelle-main"),
        ("Partager les réglages avec l'équipe", "profil de site", "profils"),
        ("Rédiger la méthodologie du rapport", "un paragraphe à adapter", "methodologie"),
        ("Retrouver un raccourci", "clavier et souris", "raccourcis"),
        ("Comprendre un message", "dépannage", "depannage"),
    ]),

    ("h2", "Ce guide", "ce-guide"),
    ("p", "Il s'adresse à ceux qui **utilisent** Gerbil, en post-fouille comme sur le terrain, et à ceux qui "
          "veulent **comprendre** ce qu'il fait pour l'expliquer dans un rapport. Le code lui-même a son propre "
          "guide, le *Guide du code*."),
    ("ul", ["[[apercu|Gerbil en un coup d'œil]] : ce que fait le programme, le parcours de A à Z, la fenêtre.",
            "[[prise-de-vue|Bien photographier]] : ce qui se joue avant Gerbil.",
            "[[etapes|Les six étapes]] : chaque page de la fenêtre, en détail, avec ses captures.",
            "[[workflows|Workflows]] : des recettes complètes, du mobilier au versement.",
            "[[comprendre|Comprendre les traitements]] : les méthodes, en mots simples, pour une méthodologie.",
            "[[inspirations|Inspirations et sources]] : d'où viennent les choix de Gerbil.",
            "[[annexes|Annexes]] : raccourcis, options, fichiers, dépannage, lexique, bibliothèques."]),
    ("h3", "Conventions"),
    ("table", [["Écrit", "Signifie"],
               ["*Lancer*", "un bouton, une case, un menu de Gerbil (en italique, avec son nom à l'écran)."],
               ["{{Ctrl+Z}}", "une touche ou une combinaison de touches."],
               ["`outlined_result`", "un nom de fichier ou de dossier, une option, du texte à taper."],
               ["[[raccourcis|Raccourcis]]", "un renvoi : un clic mène à la page citée. Les signets du PDF "
                                             "donnent aussi tout le plan."]], [0.3, 0.7]),
    ("note", "L'interface existe en français et en anglais ; ce guide donne les noms français des boutons. "
             "Les captures montrent la version 2.3 sur un vrai lot d'essai : 13 tessons photographiés au Nikon "
             "D850 avec une échelle à damier de 10 cm et une étiquette."),

    # ------------------------------------------------------------------------------------------------ 2
    ("part", "2", "Gerbil en un coup d'œil", "Ce que fait le programme, le chemin d'une série de photographies "
     "de A à Z, et la fenêtre qui le suit pas à pas.", "apercu"),

    ("h2", "Ce que fait Gerbil", "ce-que-fait-gerbil"),
    ("p", "On donne à Gerbil des photographies d'objets (céramique, métal, lithique, os, verre…) posés sur un "
          "fond uni **avec une échelle**, ou des photographies de terrain. Il :"),
    ("ol", ["**trouve et mesure l'échelle** de chaque photographie (damier, rangée simple, réglet millimétré, "
            "ou une échelle qu'on lui a apprise) : combien de pixels font un centimètre sur *cette* photo ;",
            "**détoure l'objet**, en écartant étiquettes, supports, chartes couleur et l'échelle elle-même ;",
            "**écrit des fichiers au 1:1** : un PSD à calques et des TIFF transparents dont la résolution est la "
            "vraie, pour que l'objet s'affiche à sa taille réelle dans Illustrator, Photoshop ou InDesign ;",
            "**nomme et documente** les fichiers d'après le renommage en lot (site, US, numéro…) et inscrit les "
            "métadonnées IPTC lues par Bridge, Lightroom ou l'Explorateur ;",
            "**convertit les RAW en DNG** d'archive, avec leurs métadonnées, leurs nouveaux noms et un JPG ;",
            "**compose les planches** à l'échelle (1:1, 1:2, 1:3…), les planches libres de terrain, les "
            "planches-contact, l'inventaire et les vignettes ;",
            "**contrôle un dossier avant versement** : formats, noms, doublons, sommes de contrôle ;",
            "**signale ses doutes** au lieu de se taire : tout ce qui mérite un coup d'œil porte le suffixe "
            "`_to_be_verified`."]),
    ("p", "La mesure vient de l'échelle de chaque photographie, pas des données de l'appareil : l'objectif et la "
          "distance n'ont aucune importance. Les photographies originales ne sont **jamais modifiées**."),
    ("figure", "fig_control", "L'aperçu de contrôle d'une photographie : contour du détourage en vert, étiquette "
                              "écartée en rouge, échelle trouvée en magenta, centimètres lus en orange, mesure "
                              "écrite en haut."),

    ("h2", "Le parcours de A à Z", "parcours"),
    ("p", "La fenêtre de Gerbil suit le travail en six étapes. Seule la première est indispensable ; les autres "
          "se font selon le besoin, et dans l'ordre que l'on veut. Un clic sur une carte mène à sa page."),
    ("flow", [
        ("01", "Photographies sources", "Les dossiers ou photographies à traiter, et le profil du site.", "etape-01"),
        ("02", "Nommage et métadonnées", "Les noms des fichiers produits, les informations de chaque photo ; "
                                         "puis leur relecture.", "etape-02"),
        ("03", "Détourer et mettre à l'échelle", "Les objets au 1:1 en PSD et TIFF ; puis la vérification "
                                                 "des cas douteux.", "etape-03"),
        ("04", "Convertir", "Les RAW en DNG d'archive, avec un JPG et, si on veut, un TIFF 16 bits.", "etape-04"),
        ("05", "Revue finale", "Tous les fichiers produits, et le contrôle avant versement.", "etape-05"),
        ("06", "Publication", "Planches à l'échelle, planches libres, planches-contact, inventaire, "
                              "vignettes.", "etape-06"),
    ]),
    ("table", [["", "On fait", "On obtient"],
               ["**Avant**", "[[prise-de-vue|Photographier]] avec une échelle dans le plan de l'objet, sur un "
                             "fond uni.", "Des photographies que Gerbil sait mesurer."],
               ["**01**", "Ajouter le dossier, choisir le profil du site.", "La liste des photographies."],
               ["**02**", "Remplir le renommage en lot, ou importer l'inventaire.", "Des noms de fichiers et des "
                                                                                    "métadonnées justes."],
               ["**03**", "*Lancer*, puis *Vérifier* les photographies signalées.", "`outlined_result` : PSD, TIFF "
                                                                                     "au 1:1, rapport CSV."],
               ["**04**", "*Convertir* les RAW.", "`<date>\\DNG`, `<date>\\JPG`, `<date>\\TIFF`."],
               ["**05**", "Revoir les fichiers ; contrôler avant versement.", "`deposit_check` : inventaire, "
                                                                               "sommes de contrôle."],
               ["**06**", "Composer les planches, l'inventaire, les vignettes.", "SVG, TIFF, JPEG, PDF, CSV."]],
     [0.12, 0.5, 0.38]),
    ("tip", "Une équipe qui ne fait que convertir (protocole d'une mission de terrain) passe de 02 à 04 : son "
            "profil de site marque l'étape 03 comme facultative et *Continuer* va droit à la conversion."),

    ("h2", "La fenêtre", "la-fenetre"),
    ("shot", "sources", "La fenêtre de Gerbil, ici à l'étape 01 : la colonne des étapes à gauche, la page de "
                        "l'étape à droite, sur le papier quadrillé."),
    ("ul", ["**La colonne des étapes** : un clic ouvre une étape. Sous chaque titre, un résumé tenu à jour "
            "(« 6 photographie(s) », « 4 ok, 2 à vérifier ») ; une pastille orange compte ce qu'il reste à "
            "revoir. Deux étapes ont une seconde page, en retrait : *Relire les métadonnées* et *Voir les "
            "résultats*.",
            "**La page** : un titre, une phrase qui dit à quoi sert l'étape, puis ses cartes. Laisser la souris "
            "sur un réglage affiche son explication.",
            "**Continuer** (vert clair, en bas) mène à l'étape suivante utile.",
            "**En bas de la colonne** : la langue (*FR*, *EN*), *Aide* (ce guide), le thème (*VERT*, "
            "*VIOLET*, *CLAIR*, *SOMBRE*), la version."]),

    ("h2", "Langue et thèmes", "themes"),
    ("p", "L'interface existe en français et en anglais ; la première fois, elle suit la langue de Windows. Elle "
          "se présente en vert (par défaut) ou en violet, en clair ou en sombre : un clic sur *VERT*, *VIOLET*, "
          "*CLAIR* ou *SOMBRE* change aussitôt la fenêtre, et le choix est gardé. Les fenêtres déjà ouvertes "
          "prennent les nouvelles couleurs quand on les rouvre. Les fichiers produits (planches, PDF) restent "
          "sur fond blanc, quel que soit le thème."),
    ("shot", "dark", "Le thème vert sombre, à l'étape 03."),

    ("h2", "Installer, mettre à jour, désinstaller", "installer"),
    ("h3", "Sur un ordinateur sans Python (le plus simple)"),
    ("ol", ["Double-cliquer sur **Gerbil_Setup.exe** (un seul fichier, environ 100 Mo).",
            "Garder le dossier proposé (pas besoin des droits d'administrateur), cocher si on veut le raccourci "
            "sur le bureau, puis *Install*.",
            "Ouvrir Gerbil depuis le menu Démarrer."]),
    ("warn", "Les programmes ne sont pas signés : au premier lancement, Windows peut afficher « Windows a protégé "
             "votre ordinateur ». Cliquer sur *Informations complémentaires*, puis *Exécuter quand même*."),
    ("p", "**Mettre à jour** : lancer un Gerbil_Setup.exe plus récent ; les modèles d'IA déjà téléchargés sont "
          "gardés. **Désinstaller** : *Paramètres > Applications > Applications installées*. Les photographies et "
          "les résultats ne sont jamais touchés."),
    ("h3", "Avec les scripts Python"),
    ("p", "Copier le dossier du programme, double-cliquer une fois sur **Install.bat** (il installe Python si "
          "besoin, puis numpy, OpenCV, Pillow et rawpy), puis ouvrir l'interface avec **Gerbil.bat**. "
          "**Gerbil_drop.bat** traite directement les dossiers que l'on dépose sur lui."),
    ("h3", "Ce qu'il faut à côté"),
    ("ul", ["**Adobe DNG Converter** (gratuit, chez Adobe) pour l'étape 04 seulement ; Gerbil le trouve tout seul "
            "une fois installé.",
            "**ExifTool** est fourni avec Gerbil (métadonnées des DNG).",
            "**Inkscape** (gratuit), si l'on place des dessins `.ai`, `.pdf` ou `.eps` sur les planches.",
            "Les **modèles d'IA** (détourage par l'IA, détourage en un clic) se téléchargent une fois, à la "
            "première utilisation, puis tout se fait sur l'ordinateur."]),

    # ------------------------------------------------------------------------------------------------ 3
    ("part", "3", "Bien photographier", "Gerbil mesure ce qu'il voit : la qualité du résultat se décide à la "
     "prise de vue. Quelques règles simples suffisent.", "prise-de-vue"),

    ("h2", "Les cinq règles", "cinq-regles"),
    ("ol", ["**L'échelle dans le plan de l'objet**, à la hauteur de la face photographiée. Posée sur la table sous "
            "un objet épais, elle donne une mesure fausse (l'objet est plus près de l'objectif).",
            "**Un fond uni** et différent de l'objet : clair (papier, carton) ou sombre (velours noir, feutre). "
            "Un léger dégradé d'éclairage ne gêne pas.",
            "**Une échelle reconnue** : damier noir et blanc (ou rouge) de 5, 10 ou 20 cm, à une ou deux "
            "rangées, chiffres imprimés acceptés ; rangée simple ; réglet gradué en millimètres. Une autre "
            "échelle s'[[profils|apprend]].",
            "**L'objet entier dans le cadre**, sans toucher le bord de la photographie.",
            "**L'appareil parallèle à la table** : de face, pas en oblique."]),
    ("figure", "fig_photo", "Une photographie à traiter : le tesson, son étiquette et une échelle à damier de "
                            "10 cm, sur fond clair."),
    ("h2", "Formats", "formats"),
    ("p", "JPEG, TIFF, PNG ou RAW (DNG, CR2, CR3, NEF, ARW, ORF, RW2, RAF…). Un RAW est développé par Gerbil ; "
          "pour un rendu des couleurs très précis, le développer soi-même (Lightroom, darktable) et donner les "
          "TIFF à Gerbil."),
    ("h2", "Petits conseils", "conseils"),
    ("ul", ["**Pâte à fixe** : une pâte bleue, ou cachée derrière l'objet, n'est pas confondue avec un objet clair.",
            "**Objets très clairs** (pâte blanche, craie, cortex) : sur un fond gris ou noir, ou détourage par "
            "l'IA.",
            "**Une charte couleur** dans le champ permet ensuite d'équilibrer les blancs "
            "([[couleurs|réglage Couleur]]).",
            "**Une étiquette** peut rester sur la photographie : Gerbil l'écarte. La placer de l'autre côté de "
            "l'échelle aide.",
            "**Plusieurs objets** sur une même photographie sont détourés ensemble, chacun à l'échelle."]),

    # ------------------------------------------------------------------------------------------------ 4
    ("part", "4", "Les six étapes", "Chaque page de la fenêtre en détail : ce qu'on y fait, ce qu'on y règle, ce "
     "qui en sort.", "etapes"),

    ("h2", "01 Photographies sources", "etape-01"),
    ("p", "La liste des dossiers et photographies à traiter, et le profil du site."),
    ("ul", ["*Ajouter un dossier…* (sous-dossiers compris) ou *Ajouter des photographies…* ; le nombre de "
            "photographies s'affiche.",
            "**Coller un chemin** dans le champ *ou coller un chemin* puis *Ajouter* ou {{Entrée}}.",
            "**Déposer des dossiers** sur l'icône de Gerbil les ajoute au démarrage.",
            "*Retirer* (ou {{Suppr}}) enlève la ligne choisie, *Vider* toute la liste. Les fichiers ne sont "
            "jamais touchés."]),
    ("p", "À droite, **le profil de site** et **ce qu'il contient** : son travail (détourage ou conversion), ses "
          "champs (les obligatoires ont une étoile), son modèle de nom, ses listes de mots-clés, ses réglages, "
          "ses échelles apprises."),

    ("h2", "Profils de site et échelles apprises", "profils"),
    ("p", "Un **profil de site** rassemble ce que l'on sait des photographies d'un site ou d'une campagne, choisi "
          "une fois pour toutes (*Nouveau…*, *Modifier…*, *Importer…*) :"),
    ("ul", ["le **fond** : trouvé par Gerbil, clair, ou sombre ;",
            "le **renommage** : champs, sens de chaque champ et son champ IPTC, contrôles (une US en chiffres "
            "seuls…), modèle de nom, listes de mots-clés à cocher ;",
            "les **réglages** de la fenêtre (*Garder les réglages de la fenêtre principale*) et le **travail** "
            "de l'équipe (détourage, ou conversion seule) ;",
            "les **échelles apprises** : *Apprendre une échelle à partir d'une photographie…*, cliquer les deux "
            "extrémités de l'échelle et donner la largeur de sa bande imprimée ; Gerbil la retrouve ensuite sur "
            "les autres photographies."]),
    ("p", "Par défaut, une échelle apprise est une seconde chance, utilisée quand la lecture habituelle échoue ; "
          "*Chercher d'abord les échelles apprises* l'utilise en premier. *Poser à côté des photographies…* "
          "copie le profil en `gerbil_profile.json` dans un dossier : il s'applique alors à ces photographies, "
          "pour toute l'équipe. *Importer…* ajoute à la bibliothèque un profil reçu (un fichier `.json`)."),
    ("shot", "profile", "La fenêtre d'un profil de site : fond, échelles apprises, réglages gardés.", "third"),
    ("tip", "Apprendre **chaque exemplaire** d'échelle utilisé : deux impressions du même modèle peuvent "
            "différer de 1 %."),

    ("h2", "02 Nommage et métadonnées", "etape-02"),
    ("p", "La page résume le renommage en lot du dossier ; *Ouvrir le renommage en lot…* ouvre la fenêtre qui "
          "associe à chaque photographie ses informations et le nom de ses fichiers. Seules les photographies de "
          "l'étape 01 y sont montrées (une case montre tout le dossier)."),
    ("shot", "project", "La fenêtre du renommage en lot : les champs et le modèle de nom en haut, l'assistant de "
                        "règle à droite, les valeurs communes, puis une ligne par photographie avec son nom de "
                        "sortie. Les lignes incomplètes sont en orange.", "half"),
    ("h3", "Champs, modèle de nom, règle"),
    ("ul", ["**Champs** : par défaut *Site*, *Sector*, *US*, *Object number*, *Material*, *View* ; ceux du "
            "profil sinon. *Ajouter un champ…*, *Modifier le champ…* (nom, sens, champ IPTC, obligatoire).",
            "**Modèle de nom**, par exemple `{site}_US{us}_{number}_{material}` : les fichiers produits prennent "
            "ce nom (`EX24_US1043_1_céramique_outlined.tif`). Les boutons *Insérer* ajoutent un champ. "
            "`{building|first}` garde, de plusieurs valeurs (`B27 ; B20`), celle au plus petit numéro. "
            "**Les photographies originales ne sont jamais renommées.**",
            "**Règle de nommage** (facultative) : une expression régulière, lue comme le `-match` de "
            "PowerShell. L'assistant l'écrit à partir de cases à cocher (majuscules seulement, se termine par un "
            "nombre…) et montre la ligne PowerShell équivalente, pour apprendre. *Tester un nom* l'essaie.",
            "**Noms sans accents** (case de l'assistant) : « céramique » devient « ceramique » dans les fichiers "
            "produits. À cocher avant un versement : la plupart des services d'archives refusent les accents, et "
            "*Relire les métadonnées* signale un nom qui en porte."]),
    ("h3", "Remplir les valeurs comme dans Excel"),
    ("ul", ["**Valeurs pour toutes les photographies** : le site, la campagne, l'auteur.",
            "**Le tableau** : double-clic pour modifier une case ({{Entrée}} valide, {{Échap}} annule) ; la "
            "**poignée** au coin d'une case recopie vers le bas (avec {{Ctrl}} : une série 187, 188, 189…) ; "
            "{{Ctrl+D}} recopie la première ligne choisie ; {{Ctrl+A}} choisit tout.",
            "*Appliquer à la sélection…*, *Numéroter la sélection…* ; dans *Mots-clés…*, un champ cherche un mot-clé.",
            "*Importer CSV / Excel…* : un inventaire dont la première ligne porte les noms de colonnes ; la colonne "
            "des noms de photographies est trouvée toute seule.",
            "*Mots-clés…* : les listes du profil, à cocher pour les lignes choisies."]),
    ("p", "*Enregistrer* garde le renommage (en mémoire pour une conversion, dans `gerbil_project.json` pour un "
          "détourage) ; *Enregistrer et traiter les photographies* lance aussitôt l'étape du profil."),

    ("h2", "Relire les métadonnées", "relire"),
    ("p", "La seconde page de l'étape 02 relit, avant tout traitement, chaque photographie de l'étape 01 : son "
          "nom produit et ce qu'il faut noter. Un double-clic ouvre le renommage en lot sur cette photographie."),
    ("shot", "meta", "Relire les métadonnées : en orange, une information obligatoire manque."),
    ("table", [["Remarque", "Sens", "La photographie est"],
               ["*Information manquante : Site, US*", "un champ obligatoire du profil est vide", "à vérifier"],
               ["*Valeur mal écrite : US 1043a*", "la valeur ne suit pas le contrôle de son champ", "à vérifier"],
               ["*Non renseigné : Matière*", "un champ facultatif est vide : seulement signalé", "ok"]],
     [0.38, 0.42, 0.2]),

    ("h2", "Métadonnées IPTC", "iptc"),
    ("p", "*Métadonnées IPTC…* (dans le renommage en lot) remplit les champs standard des photothèques : titre, "
          "description, mots-clés, auteur, copyright, lieu… Pour chacun, un texte où `{champ}` est remplacé par la "
          "valeur de la photographie et `{name}` par le nom de sortie ; un texte sans accolades est le même pour "
          "toutes (copyright, auteur). Ils sont écrits dans les PSD, TIFF, DNG et JPG produits, dans la copie de "
          "l'original (sans recompresser l'image) et, si coché, dans un fichier `NOM.xmp` à côté de chaque "
          "original. Un `.xmp` écrit par un autre logiciel n'est jamais remplacé."),

    ("h2", "03 Détourer et mettre à l'échelle", "etape-03"),
    ("p", "Le cœur de Gerbil : l'échelle de chaque photographie, le détourage de l'objet, les fichiers au 1:1. "
          "Garder les réglages par défaut pour un premier essai, puis *Lancer*."),
    ("shot", "cutout", "L'étape 03 après un traitement : la mire de progression, une ligne par photographie "
                       "(vert : ok, orange : à vérifier, rouge : échec), les réglages à droite."),
    ("table", [["Réglage", "Choix"],
               ["*Détourage*", "*par la couleur* (rapide, exact sur fond uni) ; *ai* ou *ai-lite* : le réseau "
                               "BiRefNet désigne les objets ([[ia|voir]])."],
               ["*Couleur*", "*inchangée* ; *balance* des blancs ; *exposure* : balance et même clarté pour "
                             "toute la série ([[couleurs|voir]])."],
               ["*Blanc de référence*", "*charte couleur*, *échelle* ou *fond*."],
               ["*Fichier Photoshop (.psd)*", "un PSD à calques en plus des TIFF."],
               ["*Fond des TIFF*", "transparent ou blanc."],
               ["*Chercher l'échelle*", "décocher pour des photographies sans échelle."],
               ["*Réglages avancés…*", "marges, mise en page de l'échelle, pâte à fixe, compression, second avis "
                                       "de l'IA, photographies en parallèle…"],
               ["*Résultats*", "*à côté des photographies* (dossier `outlined_result`) ou dans un dossier choisi."]],
     [0.3, 0.7]),
    ("p", "*Modifié par rapport au défaut* rappelle ce qui a été changé ; *Revenir aux valeurs par défaut* "
          "annule tout. Compter 3 à 4 secondes par photographie ; plusieurs sont traitées en même temps."),

    ("h2", "Ce qui sort", "ce-qui-sort"),
    ("p", "Tous les fichiers d'une photographie gardent son nom (ou le nom du renommage en lot), pour se suivre "
          "dans l'Explorateur :"),
    ("table", [["Fichier", "Contenu"],
               ["`NOM.JPG`", "Copie de la photographie originale, avec ses métadonnées IPTC (sans recompression)."],
               ["`NOM.psd`", "Photoshop à calques : *Original photo* (masqué), *Scale*, *Object*, avec des masques "
                             "de fusion modifiables au pinceau (blanc : montrer, noir : cacher)."],
               ["`NOM_outlined.tif`", "L'objet seul, fond transparent, à la résolution 1:1."],
               ["`NOM_outlined_scale.tif`", "L'objet et son échelle redressée dessous."],
               ["`to_control/NOM_to_control.jpg`", "L'aperçu de contrôle."],
               ["`outlined_report.csv`", "Le rapport : une ligne par photographie ([[rapport|colonnes]])."]],
     [0.38, 0.62]),
    ("table", [["Couleur de l'aperçu", "Signification"],
               ["Vert", "contour du détourage"], ["Magenta", "cadre de l'échelle trouvée"],
               ["Orange", "centimètres lus sur l'échelle"],
               ["Rouge", "ce qui a été écarté (étiquette, charte, petit élément isolé) ou pâte à fixe possible"],
               ["Bleu", "support en plexiglas ou ombre portée retirés"],
               ["Cyan", "fond retiré par le second avis de l'IA"]], [0.3, 0.7]),
    ("h3", "Le suffixe _to_be_verified"),
    ("p", "Quand quelque chose est douteux, tous les fichiers de la photographie reçoivent ce suffixe "
          "(`NOM_outlined_to_be_verified.tif`) : taper `to_be_verified` dans la recherche de l'Explorateur pour "
          "les retrouver. Il y a doute quand l'échelle n'est pas trouvée ou est irrégulière, quand une zone "
          "ressemble à de la pâte à fixe, qu'une charte touche l'objet, que l'objet touche le bord, qu'une "
          "information obligatoire manque ou que le nom ne suit pas la règle. Le suffixe disparaît au "
          "traitement suivant si le doute est levé."),

    ("h2", "Voir les résultats et corriger", "verifier"),
    ("p", "La seconde page de l'étape 03 liste les photographies à revoir avec leur problème. *Vérifier* ouvre la "
          "fenêtre de correction ; un double-clic sur une ligne ouvre directement ce qu'il faut corriger "
          "(l'échelle, le renommage ou le détourage)."),
    ("shot", "review", "La fenêtre de vérification : les photographies douteuses d'abord, le contour du détourage "
                       "en vert et celui de l'échelle en magenta, les outils à droite."),
    ("table", [["Outil", "Usage"],
               ["*Un clic sur l'objet (plus précis)*", "cliquer sur chaque objet à garder : Segment Anything le "
                    "détoure ({{Maj}} + clic en retire un). Le plus sûr sur les photographies difficiles, parce "
                    "qu'on **indique** l'objet au lieu de le laisser deviner."],
               ["*Effacer* / *Ajouter*", "au pinceau (taille réglable) ou au lasso."],
               ["*Retirer un morceau*", "un clic retire un morceau entier (ombre, tache du fond)."],
               ["*Orienter*", "tracer un trait le long de la lèvre : il devient horizontal, l'objet dessous ; ou "
                              "tourner par quarts de tour."],
               ["*Annuler*, *Réinitialiser la photographie*", "la dernière action ({{Ctrl+Z}}), ou toutes."],
               ["*Corriger l'échelle…*", "ouvre l'échelle manuelle de la photographie."],
               ["*Informations*", "les champs du renommage, modifiables ici."],
               ["*Valider et suivante*", "enregistre et **réexporte la photographie aussitôt**, en arrière-plan."]],
     [0.34, 0.66]),
    ("p", "*Refaire avec l'IA…* détoure à nouveau, avec le [[ia|détourage par l'IA]], les photographies à "
          "vérifier (ou celles choisies dans la liste) : c'est souvent tout ce qu'il faut pour une ombre portée, le "
          "bord de la table ou un objet blanc sur fond blanc. Le réglage de la fenêtre ne change pas."),
    ("p", "Navigation : molette pour zoomer ; bouton droit ou du milieu, {{Espace}} + glisser ou les flèches pour "
          "déplacer la vue ; {{R}} pour revoir la photographie entière."),
    ("note", "Les corrections sont gardées **à côté des photographies**, dans `gerbil_edits` : les traitements "
             "suivants les reprennent. Garder ce dossier avec les photographies."),

    ("h2", "Donner l'échelle à la main", "echelle-main"),
    ("p", "Quand l'échelle n'est pas trouvée ou mal lue : *Régler l'échelle à la main…*, cliquer les deux "
          "extrémités d'une longueur connue (0 et 5 cm, au milieu de l'échelle), donner cette longueur et la "
          "largeur de l'échelle, puis *Enregistrer*. L'échelle est gardée dans `gerbil_scales.json` et l'emporte "
          "sur la recherche automatique (rapport : `scale_type = manual`). En fin de traitement, Gerbil propose "
          "de régler à la suite toutes les échelles non trouvées (*Enregistrer et suivante*, *Passer cette "
          "photographie*, *Arrêter*)."),
    ("shot", "scale", "L'échelle à la main : deux clics sur une longueur connue, puis sa longueur et la largeur "
                      "de l'échelle.", "half"),

    ("h2", "04 Convertir : RAW en DNG", "etape-04"),
    ("p", "Pour archiver les RAW en DNG avec leurs métadonnées (le protocole « Convert RAW to DNG » de la mission "
          "MAFKF / QSR, repris dans Gerbil). Chaque RAW de l'étape 01 est converti par **Adobe DNG Converter** aux "
          "réglages du protocole (DNG 1.7, RAW d'origine intégré, aperçu moyen), sous le **nom du renommage en "
          "lot**."),
    ("shot", "convert", "L'étape 04 : la conversion à gauche, les exports supplémentaires à droite."),
    ("ul", ["Rangement par date de prise de vue : `<date>\\DNG`, `<date>\\JPG` et, si coché, `<date>\\TIFF` "
            "(16 bits, pleine taille).",
            "**JPG** : l'aperçu du DNG (~1024 px, par défaut), développé en pleine taille, ou aucun. Métadonnées "
            "intégrées dans chaque fichier.",
            "Le **XMP** voisin du RAW (Lightroom, Bridge) est intégré au DNG ; les champs remplis dans Gerbil "
            "l'emportent et les **mots-clés s'ajoutent**.",
            "**Rien n'est écrit à côté des photographies** : chaque DNG garde son RAW d'origine et les valeurs "
            "données ; rouvert plus tard, le renommage en lot d'un dossier converti se **relit dans ses DNG**.",
            "**Relancer ne refait que ce qui a changé** : un DNG déjà fait est renommé (avec son JPG et son TIFF) "
            "si son nom a changé, et ses métadonnées réécrites si les valeurs ont changé.",
            "Les champs facultatifs vides sont seulement signalés ; seuls les champs obligatoires du profil "
            "mettent une photographie à vérifier."]),

    ("h2", "05 Revue finale et versement", "etape-05"),
    ("p", "Tous les fichiers produits pour les photographies de l'étape 01, chacun avec sa nature (TIFF 1:1, PSD, "
          "aperçu, copie de l'original, planche, vignette, DNG, JPG, TIFF) ; un double-clic en ouvre un, *Ouvrir "
          "les résultats* montre les dossiers dans l'Explorateur."),
    ("shot", "final", "La revue finale : chaque fichier produit, et le contrôle avant versement."),
    ("p", "*Contrôler avant versement…* vérifie un dossier avant sa remise à un service d'archives, **sans rien "
          "copier, déplacer ni modifier**. Pour chaque fichier : son **format** (d'après la liste des extensions "
          "acceptées, à adapter au service), son **nom** (lettres sans accent, chiffres, `_`, `-`, `.`, et la "
          "règle de nommage du projet), un fichier **vide**, un **chemin** trop long (plus de 240 caractères), le "
          "**même contenu présent deux fois**. Le dossier `deposit_check` reçoit l'inventaire "
          "(`deposit_inventory.csv`, avec la somme de contrôle SHA-256 de chaque fichier), `checksums.sha256` "
          "(pour vérifier le versement après transfert) et un rapport lisible (`deposit_report.txt`)."),
    ("shot", "deposit_done", "Le contrôle avant versement : le dossier, les formats acceptés, et le bilan.",
     "half"),
    ("warn", "Ce contrôle ne remplace pas le protocole de versement du service d'archives."),

    ("h2", "06 Publication", "etape-06"),
    ("p", "Les sorties pour le rapport et la publication, chacune dans sa fenêtre."),
    ("shot", "publication", "L'étape 06 : planches, planches libres, planches-contact, inventaire, vignettes."),

    ("h2", "Les planches à l'échelle", "planches"),
    ("p", "*Planches* met en page les objets détourés d'un dossier de résultats à une échelle choisie (1:1, 1:2, "
          "1:3…) et les écrit en **SVG**, qui s'ouvrent dans Illustrator ou Inkscape à leur vraie taille : 1 cm "
          "de l'objet vaut 1 cm ÷ échelle sur le papier. *Fichiers écrits* donne aussi chaque page en **TIFF** ou "
          "**JPEG** (300 à 1200 ppp) et toutes les planches dans un **PDF**."),
    ("shot", "plates", "La fenêtre des planches : les réglages en trois onglets, l'aperçu exact de la page à "
                       "droite.", "half"),
    ("ul", ["Objets en **rangées**, dans l'ordre choisi (nom, US, matière…), avec une **légende** "
            "(`{name}`, ou `{site}_{us}_{number}`…) ; *Grouper par* commence une rangée ou une page à chaque "
            "valeur.",
            "**Barre d'échelle** réglée comme dans QGIS (style, longueur, segments, couleurs, police), gardée comme "
            "style maison.",
            "**Une échelle par planche** ; un objet trop grand passe au 1:1,5, 1:2, 1:3… sur ses propres planches. "
            "*Échelle par objet…*, ou un clic sur un objet de l'aperçu, choisit son échelle.",
            "**Échelle par matière** : céramique et verre au 1/3, fer aux 2/3, pierre au 1/3 par défaut (règles "
            "`mot=réduction` modifiables), selon les normes du dessin archéologique.",
            "**Dessins à côté des photographies** : un dossier de dessins (`.svg`, ou `.ai` `.pdf` `.eps` "
            "convertis par Inkscape) ; un dessin nommé comme l'objet est placé à côté de sa photographie, à la "
            "même échelle, en vectoriel.",
            "**Titre** et **noms de fichiers** par modèles (`{page}`, `{pages}`, `{group}`, `{scale}`) ; "
            "**cotes** en option sur un calque masqué.",
            "**Liste des figures** : `figures.csv`, écrit à côté des planches (numéro, fichier, titre, légende, "
            "échelle, crédit), se colle dans le rapport comme un tableau."]),
    ("p", "Dans l'aperçu, la molette zoome, ◀ ▶ tournent les pages."),

    ("h2", "Planches libres : terrain et orthophotos", "planches-libres"),
    ("p", "*Planches libres* met en page des **photographies entières** (sépultures, structures, orthophotos), "
          "chacune ramenée à l'échelle de la planche (1:10, 1:20, 1:50…) : une planche typologique montre ainsi "
          "les sépultures à la même échelle, rangées par type."),
    ("ul", ["*Échelle des photographies…* liste les photographies avec leur taille réelle ; un double-clic ouvre "
            "une photographie : cliquer les deux extrémités d'une longueur connue (jalon, mire, longueur de la "
            "fosse mesurée sur le terrain) et la donner en centimètres.",
            "Une **orthophoto** avec son fichier de géoréférencement (`.jgw`, `.tfw`) n'a besoin de rien.",
            "**Un clic sur une photographie de l'aperçu** : choisir son échelle (1:5 à 1:100) ou la mesurer.",
            "**Légendes, ordre et groupes** viennent du renommage en lot du dossier (ajouter *Sépulture*, *Type*, "
            "*Phase*…), puis *Grouper par : Type*.",
            "Pages A4 à A2, portrait ou paysage ; barre d'échelle en cm ou en m ; SVG, TIFF, JPEG ou PDF."]),
    ("warn", "L'échelle vaut dans le plan des deux points cliqués : une photographie prise en oblique n'est pas "
             "une orthophoto."),

    ("h2", "Planches-contact, inventaire, vignettes", "planches-contact"),
    ("ul", ["**Planches-contact** : toutes les photographies d'un dossier sur des pages, avec leur nom, tant par "
            "rangée ; *Grouper par* un champ (US, secteur) commence une page à chaque valeur. Les photographies "
            "n'y sont pas à l'échelle.",
            "**Inventaire** : une ligne par fichier des dossiers choisis (photographies, dessins, modèles 3D), "
            "avec dossier, type, taille, date, **les champs lus dans le nom** (même modèle que le renommage), et "
            "pour les images leur taille, résolution, date de prise de vue et appareil. La fenêtre montre la "
            "**ligne PowerShell** qui fait le même inventaire avec Windows seul.",
            "**Vignettes** : copies réduites pour les bases de données (128 à 1 024 px), PNG transparent ou JPEG "
            "sur blanc, marge transparente coupée."]),
    ("shot", "contact_done", "Les planches-contact : dossier, page, nombre par rangée, légende, groupes.", "half"),
    ("shot", "inventory_done", "L'inventaire, avec la ligne PowerShell qui fait le même avec Windows seul.", "half"),
    ("shot", "thumbnails_done", "Les vignettes : taille, format, objets détourés seulement.", "half"),

    # ------------------------------------------------------------------------------------------------ 5
    ("part", "5", "Workflows", "Des recettes complètes, de la caisse de mobilier au rapport, du terrain à "
     "l'archive. Chacune renvoie aux pages utiles.", "workflows"),

    ("h2", "Mobilier : du tesson à la planche publiée", "wf-mobilier"),
    ("ol", ["**Photographier** chaque objet avec son échelle, sur fond uni ([[cinq-regles|les cinq règles]]).",
            "**01** : ajouter le dossier de la caisse ; choisir le profil du site.",
            "**02** : *Importer CSV / Excel…* l'inventaire du mobilier, ou remplir le tableau (US, numéro, "
            "matière) ; vérifier le nom de sortie ; *Relire les métadonnées*.",
            "**03** : *Lancer*. Puis *Voir les résultats* : *Vérifier* les photographies signalées, un clic sur "
            "l'objet si besoin ; régler à la main les échelles non trouvées.",
            "**06** : *Planches*, au 1/3 pour la céramique, *Grouper par* US ; cocher *PDF* ; ajouter le dossier "
            "des dessins.",
            "**Rapport** : coller `figures.csv` et le [[methodologie|paragraphe de méthodologie]]."]),
    ("key", "Le contrôle le plus simple de la mesure : glisser `NOM_outlined_scale.tif` dans Illustrator ; "
            "l'échelle doit mesurer exactement 5 ou 10 cm avec la règle."),

    ("h2", "Terrain : archiver les RAW en DNG", "wf-terrain"),
    ("ol", ["**Importer le profil** de la mission (*Importer…*, étape 01) : champs, contrôles, modèle de nom, "
            "mots-clés, travail « conversion ».",
            "**01** : ajouter le dossier du jour.",
            "**02** : renommage en lot : *Creator* et *Area* pour toutes les photographies, puis bâtiment, "
            "structure, unité, contexte ligne par ligne ; *Mots-clés…* ; *Relire les métadonnées* jusqu'à ce que "
            "rien ne soit orange.",
            "**04** : *Convertir*, avec le JPG d'aperçu (et le TIFF si demandé).",
            "**05** : revoir les fichiers ; *Contrôler avant versement…* avant de copier sur le serveur.",
            "**Le lendemain** : un renommage corrigé se reconvertit en quelques secondes ; seuls les DNG "
            "changés sont renommés ou réécrits."]),

    ("h2", "Sépultures et structures à la même échelle", "wf-sepultures"),
    ("ol", ["Photographier chaque sépulture de face (photographie zénithale, ou orthophoto issue de la "
            "photogrammétrie) avec un jalon ou une mire.",
            "**02** : dans le renommage en lot, ajouter les champs *Sépulture*, *Type*, *Phase*.",
            "**06** : *Planches libres* ; *Échelle des photographies…* : mesurer le jalon de chacune.",
            "Échelle de la planche 1:20, *Grouper par : Type*, légende `{sepulture}` ; écrire en SVG et PDF."]),

    ("h2", "Préparer un versement", "wf-versement"),
    ("ol", ["Rassembler le dossier à verser (photographies, DNG, planches, inventaire).",
            "**05** : *Contrôler avant versement…* ; adapter la liste des formats acceptés à celle du service "
            "(TIFF, PNG, SVG, PDF/A, CSV…).",
            "Lire `deposit_report.txt` : renommer les fichiers aux noms refusés, retirer les doublons, "
            "raccourcir les chemins ; recommencer jusqu'à un rapport propre.",
            "Joindre `deposit_inventory.csv` et `checksums.sha256` au bordereau ; après transfert, le service "
            "peut vérifier chaque fichier."]),

    ("h2", "Travailler en équipe", "wf-equipe"),
    ("ul", ["**Un profil pour tout le site** : le préparer une fois, l'envoyer (fichier `.json`) ; chacun "
            "l'importe. Ou le *poser à côté des photographies* d'un dossier partagé.",
            "**Les décisions voyagent avec les photographies** : `gerbil_project.json`, `gerbil_scales.json`, "
            "`gerbil_edits` ([[fichiers-voisins|voir]]) ; pour la conversion, tout est dans les DNG.",
            "**Mêmes réglages, mêmes résultats** : un traitement relancé ailleurs donne les mêmes fichiers."]),

    ("h2", "Gros lots et ligne de commande", "wf-ligne"),
    ("p", "Le moteur se lance sans fenêtre, avec les mêmes options ([[options|liste]]) :"),
    ("code", "py gerbil.py \"D:\\Fouille\\Caisse 12\" --no-psd -j 6 --open\n"
             "gerbil_cli.exe \"D:\\Fouille\\Caisse 12\" --cutout ai\n"
             "py gerbil.py --dng \"D:\\Terrain\\2026-02-14\" --jpg preview --tiff"),
    ("p", "Déposer des dossiers sur **Gerbil_drop.bat** les traite aux réglages par défaut. "
          "`--refresh-names` applique un renommage modifié aux résultats déjà faits, sans retraiter."),

    ("h2", "Retraiter sans rien perdre", "wf-retraiter"),
    ("p", "Retraiter un dossier remplace les fichiers des photographies retraitées et **garde** les échelles "
          "données à la main, les corrections de la vérification et le renommage. Le suffixe "
          "`_to_be_verified` disparaît si le doute est levé ; la copie de l'original garde toujours son nom. "
          "Pour un simple changement de nom, `--refresh-names` (ou *Enregistrer* dans le renommage en lot, qui "
          "propose de l'appliquer) suffit."),

    # ------------------------------------------------------------------------------------------------ 6
    ("part", "6", "Comprendre les traitements", "Ce que fait Gerbil, étape par étape, sans programmation : de "
     "quoi l'expliquer, le vérifier et rédiger une méthodologie. Les seuils sont ceux du code ; "
     "docs/PSEUDOCODE.txt les détaille tous.", "comprendre"),

    ("h2", "Le chemin d'une photographie", "chemin"),
    ("ol", ["**Lecture** : la photographie est ouverte et redressée (orientation EXIF) ; un RAW est développé.",
            "**Copie réduite** à 1 500 px pour l'analyse ; les mesures fines sont refaites à pleine résolution.",
            "**Modèle du fond** : la couleur du fond en tout point.",
            "**Échelle** : manuelle si on l'a donnée, sinon cherchée (damier, réglet, fond sombre), sinon une "
            "échelle apprise.",
            "**Détourage** : ce qui diffère du fond, trié, affiné à pleine résolution.",
            "**Pâte à fixe** cherchée sur le contour ; **couleurs** corrigées si demandé.",
            "**Fichiers** : calques, PSD, TIFF au 1:1, métadonnées, aperçu, ligne du rapport."]),

    ("h2", "Voir les couleurs comme l'œil : CIELAB", "cielab"),
    ("p", "Une photographie est faite de pixels rouge, vert, bleu. Mais en RVB, deux couleurs « également "
          "différentes » pour l'œil peuvent avoir des écarts de chiffres très différents. Gerbil travaille donc "
          "en **CIELAB** : **L\\*** est la clarté (0 noir, 100 blanc), **a\\*** va du vert au rouge, **b\\*** du "
          "bleu au jaune. Une distance y correspond à peu près à ce que l'on perçoit :"),
    ("code", "d = racine( (0,5 × ΔL*)² + Δa*² + Δb*² )"),
    ("p", "La clarté ne compte que pour moitié : une **ombre douce** change surtout la clarté du fond, pas sa "
          "couleur, et reste ainsi hors de l'objet."),

    ("h2", "Le modèle du fond", "modele-fond"),
    ("p", "Le fond n'est jamais uniforme : l'éclairage fait un dégradé. Gerbil ajuste donc une **surface** qui le "
          "suit : pour L\\*, a\\* et b\\*, un polynôme de degré 2 en x et y, ajusté par **moindres carrés** sur "
          "les pixels du fond. On part de la couleur médiane (le fond est la plus grande partie), on garde les "
          "pixels proches (distance < 12), puis quatre fois on ajuste et on ne garde que ceux qui sont très "
          "proches (< 6). Si la clarté médiane du fond est sous 35, le fond est **sombre** (velours, feutre) et "
          "plusieurs règles changent."),

    ("h2", "Trouver l'objet", "trouver-objet"),
    ("ul", ["**Seuillage par hystérésis** (seuils 8 et 18) : on garde les régions plus différentes que 8 qui "
            "contiennent au moins un pixel plus différent que 18. Un bord pâle est gardé s'il tient à un objet "
            "net, une tache pâle isolée ne l'est pas (le principe du détecteur de Canny, appliqué aux régions).",
            "**Morphologie** : une *ouverture* efface poussières et fils fins, une *fermeture* bouche les petites "
            "brèches.",
            "**Trous** : un trou de la couleur du fond et d'au moins 0,02 cm² reste transparent (anse, "
            "perforation) ; les autres (reflet, concrétion claire) sont bouchés."]),

    ("h2", "Faire le tri", "tri"),
    ("p", "Tout ce qui diffère du fond n'est pas l'objet. Les morceaux trouvés sont triés :"),
    ("table", [["Élément", "Comment il est reconnu"],
               ["L'échelle", "sa zone est retirée ; un objet posé tout près est gardé s'il s'en éloigne de 8 mm et "
                             "diffère nettement du fond."],
               ["Échelle non mesurée, étiquette", "longs côtés droits à angle droit et contenu d'imprimé (noir et "
                    "blanc, peu coloré) ; sur 191 photographies libres, aucun objet écarté ainsi."],
               ["Ombre portée", "plus sombre que le fond mais de sa couleur, lisse, au bord extérieur flou "
                                "(pénombre) ; le bord d'un objet est net."],
               ["Support en plexiglas", "presque la couleur du fond, dépasse de l'objet, aussi clair ou plus blanc."],
               ["Charte couleur", "au moins 5 secteurs de teinte vive sur 12 ; une céramique peinte en couvre 2 au "
                                  "plus (1 763 photographies testées)."],
               ["Étiquettes, écritures", "de l'autre côté de l'échelle ; partout plus fines que 1,7 mm ; petits "
                                         "éléments isolés à plus de 8 mm de l'objet."],
               ["Étiquette papier sur fond sombre", "claire et rectangulaire (85 % de son rectangle) ; un tesson "
                                                    "cassé ne remplit jamais autant son rectangle."]],
     [0.3, 0.7]),
    ("figure", "fig_dark", "Sur feutre sombre (photographie synthétique) : l'étiquette papier est écartée "
                           "(contour rouge), l'objet gardé (contour vert)."),

    ("h2", "Affiner le bord", "bord"),
    ("p", "Le premier détourage, fait sur la copie réduite, est refait **à pleine résolution** dans une bande "
          "autour du contour, puis adouci (flou de 0,8 px) : un bord net sans escalier, comme un détourage à la "
          "main. Sur fond sombre, le bord est placé au milieu du dégradé et ses derniers pixels prennent la "
          "couleur de l'objet : pas de liseré sombre."),

    ("h2", "Lire une échelle à damier", "damier"),
    ("ol", ["**Repérer** l'encre : pixels noirs ou rouges, en groupes allongés (2,5 fois plus longs que larges).",
            "**Redresser** une vignette de l'échelle à l'horizontale.",
            "**Lire les cases**, colonne par colonne : quelle rangée est encrée ; les suites semblables sont les "
            "cases.",
            "**Seconde lecture** si des chiffres sont imprimés dans les cases : on ajuste un « peigne » régulier "
            "sur les limites entre cases.",
            "**Mesurer à pleine résolution**, au sous-pixel : px/cm = longueur des cases ÷ nombre de cases.",
            "**Mettre à l'endroit** : les signes imprimés (« 5 », « 10 », « cm ») sont comparés à des chiffres "
            "dessinés avec 12 polices ; sur 1 265 échelles d'orientation connue, aucune erreur."]),
    ("p", "Vérifications : longueur habituelle (5, 10 ou 20 cm), cases régulières (écart < 15 %). Une échelle "
          "coupée par le bord est mesurée sur ses cases complètes."),

    ("h2", "Lire un réglet millimétré", "reglet"),
    ("p", "Les graduations sont des traits sombres fins et parallèles : Gerbil les repère (filtre « black-hat »), "
          "les regroupe en rangées régulières et ajuste une suite x = début + pas × k sur la cinquantaine de "
          "graduations. Mesurer un pas sur ~50 intervalles donne une précision d'environ **0,1 %**."),

    ("h2", "Les échelles apprises", "apprises"),
    ("p", "On montre une fois les deux extrémités d'une échelle d'une autre forme ; Gerbil garde son image. Sur une "
          "autre photographie, il la cherche **grossièrement** par des points caractéristiques (SIFT) appariés et "
          "filtrés par **RANSAC**, puis **finement** par corrélation (ECC), ce qui mesure la longueur à mieux que "
          "0,1 % (0,05 % mesuré) quand c'est la même échelle physique."),

    ("h2", "La pâte à fixe", "pate"),
    ("p", "Gerbil cherche sur le contour deux creux qui découpent une partie de l'objet. Cette partie est de la "
          "pâte possible si elle est à la fois plus lisse, d'une autre couleur, moins colorée et plus claire que "
          "le reste. Par défaut elle est seulement signalée (zone rouge) ; `--remove-putty` la retire."),

    ("h2", "Le détourage par l'IA", "ia"),
    ("p", "Par défaut, l'objet est ce qui diffère du fond par sa couleur : rapide et exact sur un fond uni, mais "
          "une ombre portée, le bord de la table ou un objet blanc sur fond blanc le trompent. Avec *Détourage : "
          "ai*, le réseau **BiRefNet** désigne d'abord les objets ; Gerbil trie ensuite les morceaux comme "
          "d'habitude et trace toujours le bord d'après la photographie, à pleine résolution."),
    ("ul", ["Tout se fait sur l'ordinateur : aucune photographie n'est envoyée sur internet.",
            "*ai* : BiRefNet (970 Mo, téléchargé une fois), environ 8 s de plus par photographie ; *ai-lite* : "
            "réseau allégé (224 Mo), environ 4 s, un peu moins sûr sur les cas difficiles.",
            "**Second avis de l'IA** (*Réglages avancés*) : IS-Net ou BiRefNet ne peut que **retirer** du fond "
            "(perforations, écarts, halos), jamais ajouter : ses erreurs n'ont donc pas d'effet.",
            "**Un clic sur l'objet** (vérification) : **Segment Anything**, version MobileSAM (45 Mo) ; on lui "
            "dit quel objet détourer, Gerbil garde son propre bord là où les deux sont d'accord."]),

    ("h2", "Les couleurs : balance et exposition", "couleurs"),
    ("p", "Par défaut, les couleurs sont gardées. *Couleur : balance* retire la dominante de la lumière en "
          "rendant neutre un blanc de la photographie ; *exposure* amène en plus ce blanc à la même clarté sur "
          "toutes les photographies (85 % de luminance), pour une série homogène. La correction vient **après** "
          "le détourage, qui reste le même ; la copie de l'original n'est jamais modifiée."),
    ("ul", ["*charte couleur* (par défaut) : la case blanche d'une charte (SpyderCheckr, ColorChecker, "
            "Farbkarte) ou le centre blanc d'un Archaeo Colorimeter ; sans charte, pas de correction.",
            "*échelle* : quand elle est vraiment blanche (certaines sont crème).",
            "*fond* : sur papier blanc uniquement."]),
    ("note", "Ce sont des corrections de la lumière, pas un étalonnage : la lecture au code Munsell se fait "
             "toujours sur l'objet."),

    ("h2", "De la mesure au 1:1", "un-pour-un"),
    ("p", "Un fichier image porte une **résolution** (pixels par pouce) dont Illustrator se sert pour donner sa "
          "taille à une image placée. Gerbil y inscrit la résolution mesurée :"),
    ("code", "ppi = px/cm × 2,54        (1 pouce = 2,54 cm)\n"
             "exemple : 100 px/cm → 254 ppi : un objet de 600 px de large mesure 6 cm"),
    ("p", "L'image n'est jamais agrandie ni réduite : seule l'étiquette de résolution change. Le **PSD** est écrit "
          "octet par octet (masques de fusion : rien n'est effacé) ; les **TIFF** sont sans perte (LZW), avec "
          "transparence."),

    ("h2", "Les métadonnées", "metadonnees"),
    ("ul", ["**EXIF** : les informations de l'appareil (boîtier, objectif, focale, date, ouverture, ISO), "
            "recopiées.",
            "**XMP** : un paquet de texte structuré dans le fichier : la mesure de l'échelle, le nom de sortie, "
            "les champs du renommage.",
            "**IPTC Core** : les champs des photothèques (titre, mots-clés, auteur, copyright, lieu), écrits dans "
            "le XMP. Dans un JPEG, le XMP est ajouté sans toucher à l'image (vérifié pixel pour pixel)."]),

    ("h2", "La conversion en DNG", "conversion"),
    ("p", "Pour chaque RAW : la date de prise de vue range le fichier ; Adobe DNG Converter écrit le DNG sous le "
          "nom du renommage ; **ExifTool** y intègre le XMP voisin, puis les champs IPTC de Gerbil, et y garde "
          "le RAW d'origine et les valeurs données (espace XMP `gerbil`). C'est ce qui permet de tout relire "
          "dans les DNG, et de ne refaire que ce qui a changé, sans aucun fichier à côté des photographies."),

    ("h2", "Les planches : du réel au papier", "planches-papier"),
    ("p", "Chaque objet a sa taille réelle, lue dans la résolution de son TIFF ; à l'échelle 1:r, sa taille sur le "
          "papier est taille réelle ÷ r (6 cm au 1:2 font 3 cm). La page est décrite comme une liste de formes "
          "**en millimètres** ; cette même description est écrite en SVG et dessinée pour l'aperçu, qui montre "
          "donc exactement ce qui sera écrit."),

    ("h2", "Précision et limites", "limites"),
    ("ul", ["La mesure n'est juste que si l'échelle est **dans le plan de l'objet**.",
            "Le fond doit être uni et différent de l'objet ; un support opaque blanc logé dans un creux n'est pas "
            "reconnu (l'effacer dans *Vérifier*).",
            "Un objet très clair sur fond blanc peut perdre des parties : fond plus sombre, détourage par l'IA, "
            "ou un clic sur l'objet.",
            "Une autre forme d'échelle est le plus souvent signalée : l'apprendre, ou la donner à la main.",
            "Sur 1 764 photographies de référence, aucune échelle déjà trouvée n'a changé d'une version à "
            "l'autre : chaque changement du programme est vérifié au pixel près sur ces lots."]),

    ("h2", "Pour une méthodologie", "methodologie"),
    ("p", "Un paragraphe à adapter pour le rapport :"),
    ("quote", "« Les objets ont été photographiés sur fond uni avec une échelle dans le plan de la face "
              "photographiée. Les photographies ont été détourées et mises à l'échelle avec Gerbil 2.3 "
              "(Charbonnel 2026, logiciel libre, GPL v3). L'échelle de chaque photographie est détectée et "
              "mesurée automatiquement (damier : longueur des cases ajustée au sous-pixel ; réglet : pas du "
              "millimètre ajusté sur l'ensemble des graduations, précision d'environ 0,1 %), puis la résolution "
              "réelle est inscrite dans les fichiers, ce qui restitue les objets au 1:1. Le détourage repose sur "
              "la distance de couleur (CIELAB) à un modèle polynomial du fond, avec seuillage par hystérésis ; "
              "les cas douteux ont été signalés par le logiciel et vérifiés un à un. »"),

    # ------------------------------------------------------------------------------------------------ 7
    ("part", "7", "Inspirations et sources", "Les pratiques, les normes, les méthodes et les logiciels dont "
     "Gerbil reprend les idées.", "inspirations"),

    ("h2", "D'où vient Gerbil", "origine"),
    ("p", "Gerbil est né d'un geste répété des milliers de fois en post-fouille : détourer un objet dans "
          "Photoshop, puis le remettre à l'échelle à la main pour la planche. Il a grandi avec les besoins d'une "
          "équipe : les noms de fichiers et les métadonnées, puis le protocole « Convert RAW to DNG » de la "
          "mission MAFKF / QSR (Failaka, Koweït), écrit par Eloïs Charbonnel et repris tel quel à l'étape 04, "
          "puis les planches, le terrain et le versement."),
    ("p", "Trois principes le guident : **ne jamais modifier les originaux**, **dire ses doutes** plutôt que se "
          "tromper en silence, et **garder identiques au pixel près** les résultats déjà justes d'une version à "
          "l'autre."),

    ("h2", "Le dessin archéologique et les planches", "normes-dessin"),
    ("ul", ["Normes du dessin d'objets archéologiques (Bruxelles, DMS 2009) : réductions de publication, "
            "céramique et verre au 1/3, fer aux 2/3 ou au 1/3, pierre au 1/3 ou 1/6 : les **échelles par "
            "matière** des planches.",
            "M. Jean, *Le dessin archéologique* (2008) : « l'échelle graphique doit toujours être présente » : la "
            "**barre d'échelle** de chaque planche.",
            "M. Jean, *Didacticiel infographie céramique* (2010) : la céramique présentée au 1/3 et le montage "
            "des planches dans Illustrator.",
            "Arcelin et Rigoir, Feugère, Foy et Vallauri (1982), SA (2011), Prodhomme : normalisation du dessin "
            "céramologique et non céramique, préparation des publications.",
            "S. Eusèbe (Inrap), *La représentation scientifique des vestiges archéologiques* : les « détails » "
            "comme l'échelle graphique comptent."]),

    ("h2", "Les méthodes de traitement d'image", "methodes"),
    ("table", [["Méthode", "Dans Gerbil", "Référence"],
               ["CIELAB", "distance de couleur au fond", "CIE, espace L\\*a\\*b\\* (1976)"],
               ["Hystérésis", "garder les bords pâles d'un objet net", "J. Canny, *A Computational Approach to "
                                                                      "Edge Detection*, 1986"],
               ["Moindres carrés", "modèle polynomial du fond, peigne du réglet", "Legendre, Gauss"],
               ["SIFT", "retrouver une échelle apprise", "D. Lowe, *Distinctive Image Features from Scale-"
                                                         "Invariant Keypoints*, 2004"],
               ["RANSAC", "garder les correspondances qui s'accordent", "M. Fischler et R. Bolles, 1981"],
               ["ECC", "alignement fin de l'échelle apprise", "G. Evangelidis et E. Psarakis, 2008"],
               ["IS-Net", "second avis de l'IA", "X. Qin et al., *Highly Accurate Dichotomous Image "
                                                 "Segmentation*, 2022"],
               ["BiRefNet", "détourage par l'IA, second avis", "P. Zheng et al., *Bilateral Reference for "
                    "High-Resolution Dichotomous Image Segmentation*, 2024"],
               ["Segment Anything", "un clic sur l'objet", "A. Kirillov et al., 2023 ; MobileSAM : C. Zhang et "
                                                            "al., *Faster Segment Anything*, 2023"]],
     [0.2, 0.36, 0.44]),

    ("h2", "Les logiciels qui ont inspiré l'interface", "logiciels-inspiration"),
    ("ul", ["**Excel** : la poignée qui recopie une case vers le bas, les séries, {{Ctrl+D}}.",
            "**QGIS** : la barre d'échelle (style, segments, unités) des planches.",
            "**PowerShell** : la règle de nommage lue comme `-match`, et la ligne d'inventaire à copier, pour "
            "apprendre.",
            "**Bridge et Lightroom** : les champs IPTC et le XMP voisin, intégrés tels quels.",
            "**Photoshop** : le PSD à calques et masques de fusion, pour reprendre le détourage au pinceau.",
            "**Le papier millimétré** du dessinateur : le quadrillage de la fenêtre et de ce guide, et la mire "
            "de progression en damier."]),

    ("h2", "Formats, métadonnées et archivage", "formats-archivage"),
    ("ul", ["**IPTC Photo Metadata Standard** (IPTC Core), écrit en **XMP** (ISO 16684-1).",
            "**DNG** (Adobe Digital Negative), format ouvert d'archive des RAW.",
            "**CINES** : sélection des formats de conservation à long terme et outil de validation FACILE "
            "(<https://www.cines.fr/preservation/expertises/file-format/selection/>).",
            "**HEG Genève (ArchiLab)** : TIFF pour les images numérisées, PNG pour le web, SVG pour le "
            "vectoriel.",
            "**Consortium 3D (Huma-Num)** et **CND3D** : cycle de vie et archivage des données 3D, pistes pour "
            "la suite."]),

    # ------------------------------------------------------------------------------------------------ 8
    ("part", "8", "Annexes", "Tout ce que l'on cherche une fois l'habitude prise.", "annexes"),

    ("h2", "Raccourcis clavier et souris", "raccourcis"),
    ("table", [["Où", "Touche ou geste", "Effet"],
               ["Étape 01", "{{Entrée}} dans le champ du chemin", "ajoute le dossier collé"],
               ["Étape 01", "{{Suppr}}", "retire la ligne choisie"],
               ["Étape 01", "déposer des dossiers sur l'icône", "les ajoute au démarrage"],
               ["Tableaux des étapes", "double-clic sur une ligne", "ouvre ce qu'il faut corriger"],
               ["Renommage en lot", "double-clic sur une case", "la modifier ; {{Entrée}} valide, {{Échap}} "
                                                                "annule"],
               ["Renommage en lot", "glisser la poignée d'une case", "recopie vers le bas ; avec {{Ctrl}} : série"],
               ["Renommage en lot", "{{Ctrl+D}}", "recopie la première ligne choisie vers les autres"],
               ["Renommage en lot", "{{Ctrl+A}}", "choisit toutes les lignes"],
               ["Renommage en lot", "{{Ctrl}} / {{Maj}} + clic", "choisir plusieurs lignes"],
               ["Vérification", "molette", "zoom"],
               ["Vérification", "bouton droit ou du milieu, {{Espace}} + glisser, flèches", "déplacer la vue"],
               ["Vérification", "{{R}}", "photographie entière"],
               ["Vérification", "{{Ctrl+Z}}", "annuler la dernière action"],
               ["Vérification", "{{Maj}} + clic (outil un clic)", "retirer un objet"],
               ["Échelle à la main", "glisser un point", "l'ajuster ; molette : zoom ; {{R}} : tout voir"],
               ["Planches", "molette, ◀ ▶", "zoom, pages"],
               ["Planches", "clic sur un objet", "choisir son échelle"],
               ["Partout", "souris sur un réglage", "son explication"]], [0.22, 0.38, 0.4]),

    ("h2", "Options de la ligne de commande", "options"),
    ("p", "`py gerbil.py DOSSIER --option` (scripts) ou `gerbil_cli.exe DOSSIER --option` (version .exe) :"),
    ("table", [["Option", "Effet"],
               ["`-o DOSSIER`", "dossier de sortie (par défaut `outlined_result` à côté des photographies)"],
               ["`--cutout colour|ai|ai-lite`", "détourage par la couleur ou par l'IA"],
               ["`--colour none|balance|exposure`, `--white chart|scale|background`", "couleurs et blanc de "
                                                                                       "référence"],
               ["`--background white`", "TIFF sur fond blanc"],
               ["`--remove-putty`", "retire la pâte à fixe trouvée"],
               ["`--layout original`", "laisse l'échelle où elle est"],
               ["`--scale-cm 10`, `--no-scale`", "impose la longueur de l'échelle ; pas d'échelle"],
               ["`--margin-cm`, `--gap-cm`", "marge autour de l'objet, écart objet / échelle (0,5 cm)"],
               ["`--no-psd`, `--no-original-layer`, `--no-original-copy`, `--no-control`", "fichiers en moins"],
               ["`--compression lzw|zip|none`", "compression des TIFF"],
               ["`--default-ppi 300`", "résolution sans échelle"],
               ["`--ai`, `--ai-model isnet|birefnet|birefnet-lite`, `--ai-device cpu`", "second avis de l'IA"],
               ["`--profile FICHIER`", "profil de site"],
               ["`--refresh-names`", "applique un renommage modifié sans retraiter"],
               ["`-j 4`, `--open`, `-v`", "photographies en parallèle ; ouvrir à la fin ; détails des erreurs"],
               ["`--dng DOSSIER`, `--jpg preview|full|none`, `--tiff`", "conversion RAW en DNG (étape 04)"]],
     [0.5, 0.5]),

    ("h2", "Le rapport outlined_report.csv", "rapport"),
    ("p", "Une ligne par photographie, séparateur « ; » et virgule décimale (Excel français). États : `ok`, "
          "`to verify`, `failed`, `error`. Les champs du renommage s'ajoutent en colonnes."),
    ("table", [["Colonne", "Contenu"],
               ["`file`, `output_name`", "nom de la photographie, nom des fichiers produits"],
               ["`status`, `to_verify`", "état, et raisons du doute"],
               ["`scale_found`, `scale_type`", "`checkerboard`, `ruler`, `manual`, `learned`"],
               ["`squares`, `scale_length_cm`", "nombre de cases, longueur de l'échelle"],
               ["`px_per_cm`, `ppi_1_1`", "la mesure, et la résolution 1:1"],
               ["`object_width_cm`, `object_height_cm`", "dimensions de l'objet détouré"],
               ["`pieces`", "nombre de morceaux détourés"],
               ["`camera`, `lens`, `focal_mm`, `date_taken`", "prise de vue (EXIF)"],
               ["`notes`, `duration_s`", "remarques, durée"]], [0.42, 0.58]),

    ("h2", "Les fichiers écrits à côté des photographies", "fichiers-voisins"),
    ("p", "Ce que l'on décide pour un **détourage** est gardé à côté des photographies, pour qu'un traitement "
          "suivant ou un collègue le retrouve ; à archiver avec elles. La **conversion**, elle, n'écrit rien à "
          "côté : tout est dans les DNG."),
    ("table", [["Fichier", "Contenu"],
               ["`gerbil_project.json`", "renommage en lot : champs, modèle, règle, valeurs, IPTC"],
               ["`gerbil_scales.json`", "échelles données à la main"],
               ["`gerbil_edits/`", "corrections de la vérification (masques, angles)"],
               ["`gerbil_profile.json`", "profil de site posé dans le dossier"],
               ["`NOM.xmp`", "métadonnées IPTC à côté de l'original, si demandé"]], [0.35, 0.65]),

    ("h2", "Dépannage", "depannage"),
    ("table", [["Ce que l'on voit", "Ce qu'il faut faire"],
               ["« Windows a protégé votre ordinateur »", "*Informations complémentaires*, puis *Exécuter quand "
                                                          "même* (programme non signé)."],
               ["Un bandeau orange « paquets manquants »", "*Installer maintenant* (version scripts) : numpy, "
                                                           "OpenCV, Pillow, rawpy."],
               ["« Échelle non trouvée »", "vérifier qu'elle est entière et nette ; la [[echelle-main|donner à la "
                                           "main]] ou l'[[profils|apprendre]]."],
               ["Des parties d'un objet clair manquent", "fond plus sombre, *Détourage : ai*, ou un clic sur "
                                                         "l'objet dans *Vérifier*."],
               ["L'ombre est gardée avec l'objet", "*Détourage : ai*, ou *Retirer un morceau*."],
               ["« Information manquante »", "remplir les champs obligatoires du renommage en lot "
                                             "([[relire|relire]])."],
               ["Deux photographies ont le même nom de sortie", "Gerbil ajoute un suffixe ; compléter le modèle "
                                                                 "(numéro, vue)."],
               ["L'étape 04 demande Adobe DNG Converter", "l'installer (gratuit, chez Adobe), puis relancer."],
               ["Le détourage par l'IA est lent", "*ai-lite*, ou moins de photographies en parallèle."],
               ["La mesure semble fausse de quelques %", "l'échelle était-elle dans le plan de l'objet ? Contrôler "
                                                         "avec `NOM_outlined_scale.tif` dans Illustrator."]],
     [0.42, 0.58]),

    ("h2", "Lexique", "lexique"),
    ("defs", [("1:1, échelle 1:r", "1:1 : taille réelle. À l'échelle 1:3, l'objet est trois fois plus petit sur "
                                   "le papier."),
              ("Balance des blancs", "Correction qui rend neutre un blanc, pour retirer la dominante de la lumière."),
              ("Charte couleur", "Carton de couleurs de référence (SpyderCheckr, ColorChecker) photographié avec "
                                 "l'objet."),
              ("CIELAB", "Espace de couleurs proche de la perception : clarté L\\*, axes a\\* et b\\*."),
              ("Damier", "Échelle à cases de 1 cm alternées, noires et blanches (ou rouges)."),
              ("Détourage", "Séparer l'objet de son fond ; le fond devient transparent."),
              ("DNG", "Digital Negative : format ouvert d'Adobe pour archiver les RAW, avec leurs métadonnées."),
              ("EXIF", "Informations écrites par l'appareil : boîtier, objectif, date, réglages."),
              ("Hystérésis", "Seuillage à deux seuils : garder ce qui dépasse le bas s'il touche ce qui dépasse "
                             "le haut."),
              ("IPTC", "Jeu de champs standard des photothèques (titre, auteur, lieu, mots-clés…)."),
              ("Masque de fusion", "Dans un PSD, ce qui cache une partie d'un calque sans l'effacer."),
              ("Métadonnées", "Informations inscrites dans un fichier, à côté de l'image."),
              ("Orthophoto", "Image redressée, sans perspective, à échelle constante, souvent géoréférencée."),
              ("Planche", "Page de figures d'une publication, à une échelle donnée."),
              ("Planche-contact", "Toutes les photographies d'un dossier en petit, sur des pages, pour s'y "
                                  "retrouver."),
              ("Profil de site", "Ce que Gerbil sait d'un site : fond, échelles, champs, modèle de nom, réglages."),
              ("PSD", "Fichier Photoshop à calques."),
              ("px/cm, ppi", "Pixels par centimètre (mesurés sur l'échelle) ; pixels par pouce (= px/cm × 2,54), "
                             "inscrits dans les fichiers."),
              ("RAW", "Fichier brut de l'appareil (CR2, CR3, NEF, ARW…), avant développement."),
              ("Réglet", "Règle graduée en millimètres."),
              ("Renommage en lot", "Les noms et les informations de toutes les photographies d'un dossier, d'un "
                                   "coup."),
              ("Règle de nommage", "Ce que tout nom doit respecter, écrit en expression régulière."),
              ("SHA-256", "Empreinte d'un fichier : si un seul octet change, elle change ; sert à vérifier un "
                          "transfert."),
              ("SVG", "Format de dessin vectoriel, ouvert par Illustrator et Inkscape."),
              ("TIFF", "Format d'image sans perte, avec transparence : le format des objets détourés."),
              ("Versement", "Remise d'un ensemble de fichiers à un service d'archives."),
              ("Vignette", "Petite copie d'une image, pour une base de données."),
              ("XMP", "Format des métadonnées inscrites dans les fichiers (ou dans un fichier .xmp voisin).")]),

    ("h2", "Bibliothèques et logiciels", "bibliotheques"),
    ("p", "Gerbil s'appuie sur des logiciels libres ; qu'ils en soient remerciés."),
    ("table", [["Nom", "Rôle dans Gerbil", "Licence"],
               ["Python", "le langage du programme", "PSF"],
               ["numpy", "les images comme tableaux de nombres, les calculs", "BSD"],
               ["OpenCV", "traitement d'image : couleurs, morphologie, contours, SIFT, ECC", "Apache 2.0"],
               ["Pillow", "lire et écrire les images, dessiner les planches", "MIT-CMU"],
               ["rawpy, LibRaw", "développer les photographies RAW", "MIT ; LGPL 2.1 ou CDDL"],
               ["onnxruntime", "faire tourner les réseaux d'IA sur l'ordinateur", "MIT"],
               ["BiRefNet, IS-Net", "réseaux de détourage (exports ONNX de rembg)", "MIT ; Apache 2.0"],
               ["MobileSAM", "un clic sur l'objet (export ONNX d'Acly)", "MIT"],
               ["Tk (tkinter)", "les fenêtres", "licence BSD de Tcl/Tk"],
               ["ExifTool", "écrire les métadonnées des DNG (fourni)", "licence de Perl"],
               ["Adobe DNG Converter", "convertir les RAW en DNG (à installer)", "gratuit, propriétaire"],
               ["Inkscape", "convertir les dessins .ai, .pdf, .eps (facultatif)", "GPL"],
               ["PyInstaller", "fabriquer Gerbil.exe", "GPL avec exception"],
               ["Source Serif 4, Cormorant Garamond, Courier Prime", "les polices de l'interface et des guides",
                "SIL OFL"]], [0.3, 0.48, 0.22]),

    ("h2", "Citer Gerbil, licence", "citer"),
    ("p", "Charbonnel E. 2026. *Gerbil : boîte à outils photographique de l'archéologue*, version 2.3. "
          "Logiciel libre, licence GNU GPL v3 ou ultérieure. <https://github.com/EloisCharbonnel/gerbil>"),
    ("p", "Gerbil est fourni sans garantie. On peut l'utiliser, l'étudier, le modifier et le redistribuer "
          "selon les termes de la licence (fichier `LICENSE`)."),
]

# =============================================================================================================
# GUIDE DU CODE
# =============================================================================================================

CODE = [
    ("part", "1", "Le programme en grand", "Les fichiers, comment ils se parlent, et le chemin d'une photographie "
     "dans le code. Le traitement lui-même (méthodes, seuils) est décrit dans le guide de l'utilisateur et dans "
     "docs/PSEUDOCODE.txt.", "programme"),

    ("h2", "Les fichiers", "fichiers"),
    ("table", [["Fichier", "Rôle"],
               ["`gerbil.py`", "le moteur : tout ce qui traite une photographie, et la ligne de commande ; il ne "
                               "sait rien des fenêtres"],
               ["`gerbil_gui.pyw`", "l'interface : les fenêtres ; elle lance le moteur comme un programme séparé"],
               ["`gerbil_dng.py`", "la conversion RAW en DNG (Adobe DNG Converter, ExifTool)"],
               ["`gerbil_plates.py`", "les planches SVG"],
               ["`gerbil_tools.py`", "l'inventaire CSV et les vignettes"],
               ["`gerbil_lang_fr.py`", "les textes français de l'interface"],
               ["`packaging/gerbil_setup.pyw`", "l'installateur"],
               ["`tests/`", "les tests automatiques, sur des photographies synthétiques"],
               ["`docs/`", "pseudo-code, feuille de route, sources, guides et leurs générateurs"]], [0.35, 0.65]),

    ("h2", "Comment ils se parlent", "dialogue"),
    ("code", "gerbil_gui.pyw  (fenêtres)  --lance-->  gerbil.py / gerbil_cli.exe  (moteur, photo après photo)\n"
             "       |                                   |\n"
             "       |  lit les lignes affichées         +--> outlined_result/ : PSD, TIFF, aperçus, rapport\n"
             "       |  (« [3/12] NOM: ok ... »)         |\n"
             "       |                                   +--> lit gerbil_project.json, gerbil_scales.json,\n"
             "       |                                        gerbil_edits/, gerbil_profile.json\n"
             "       +--> gerbil.py --dng  -->  gerbil_dng.py  -->  Adobe DNG Converter, ExifTool\n"
             "       +--> gerbil_plates.py (planches)    gerbil_tools.py (inventaire, vignettes)"),
    ("p", "L'interface ne traite pas les photographies elle-même : elle construit la ligne de commande à partir "
          "des réglages, lance le moteur (`subprocess`) et lit les lignes qu'il affiche pour montrer "
          "l'avancement. Quelques fenêtres appellent directement des fonctions du moteur (`import gerbil`), pour "
          "lire une photographie ou apprendre une échelle. Les renommages en lot gardés en mémoire sont passés au "
          "moteur par un fichier temporaire nommé dans la variable `GERBIL_PROJECTS`."),

    ("h2", "Le chemin d'une photographie dans le code", "chemin-code"),
    ("p", "La fonction `process_photo` de `gerbil.py` appelle, dans l'ordre :"),
    ("ol", ["`load_photo` : lit le fichier (RAW par `develop_raw`), le redresse, garde EXIF et profil couleur.",
            "`BackgroundModel` : le modèle du fond, sur la copie réduite.",
            "`manual_scale`, sinon `detect_scale` (`analyze_pattern`, `analyze_comb`, `detect_ruler`, "
            "`_scale_on_dark`…), sinon `detect_learned_scale` : un objet `Scale`.",
            "`outline_object` (ou `cutout_from_mask` pour un masque corrigé à la main), puis `find_putty`.",
            "`layout`, puis `write_psd`, `write_tiff` (avec `make_xmp`), `control_image`, `write_review`.",
            "La ligne du rapport est renvoyée ; `main` écrit `outlined_report.csv` et le bilan."]),
    ("h2", "Le chemin d'une conversion", "chemin-dng"),
    ("ol", ["`gerbil.py --dng` passe la main à `gerbil_dng.main`, qui ouvre ExifTool une seule fois "
            "(`-stay_open`) avec l'espace XMP `gerbil`.",
            "`convert` groupe les RAW par dossier ; `convert_folder` lit le renommage (`gerbil.load_project`), "
            "et les DNG déjà faits (`previous_outputs`).",
            "Pour chaque RAW : la date de prise de vue, le nom, Adobe DNG Converter, le XMP voisin, les champs "
            "IPTC, le JPG (et le TIFF par `develop_to`), une ligne du rapport."]),

    ("part", "2", "Les notions de Python", "De quoi lire n'importe quelle ligne du programme.", "python"),
    ("h2", "Les notions utiles", "notions"),
    ("defs", [("Module, import", "Chaque fichier est un module. `import gerbil as g` donne accès à ses fonctions "
                                 "(`g.load_photo`) ; `from PIL import Image` prend un seul nom."),
              ("Fonction", "`def nom(arguments):` reçoit des valeurs et renvoie un résultat (`return`) ; le corps "
                           "est le bloc décalé sous la ligne `def`."),
              ("Docstring", "La première chaîne d'une fonction, entre triples guillemets : son explication. C'est "
                            "elle, traduite, que montre la référence."),
              ("Classe, méthode, self", "`class Nom:` regroupe des données et les fonctions qui travaillent dessus "
                    "(ses méthodes) ; `self` est l'objet lui-même. Chaque fenêtre est une classe : son `__init__` "
                    "la construit, ses méthodes réagissent à l'utilisateur."),
              ("@dataclass", "Une classe qui est surtout une fiche de valeurs nommées (`Scale`, `PlateSettings`)."),
              ("Dictionnaire, liste, tuple", "`{\"clé\": valeur}` : réglages, lignes du rapport, JSON ; `[a, b]` : "
                    "valeurs ordonnées ; `(x, y)` : groupe fixe."),
              ("Tableau numpy", "Une image est un tableau : `rgb[y, x]` est un pixel, `rgb.shape` vaut (hauteur, "
                    "largeur, 3). Une opération s'applique à tous les pixels d'un coup, sans boucle."),
              ("Masque", "Un tableau de vrai / faux de la taille de l'image : `rgb[masque]` donne les pixels de "
                         "l'objet."),
              ("OpenCV (cv2)", "Le traitement d'image : redimensionner, flouter, Lab, morphologie (`cv2.erode`, "
                               "`cv2.dilate`), composantes connexes, contours."),
              ("Exceptions", "`try: … except OSError:` attrape une erreur au lieu d'arrêter le programme."),
              ("f-string", "`f\"{px_cm:.2f} px/cm\"` écrit des valeurs dans un texte."),
              ("Travail en parallèle", "Le moteur traite plusieurs photographies à la fois "
                    "(`ProcessPoolExecutor`) ; l'interface reste réactive avec des fils (`threading.Thread`) et "
                    "`after(ms, fonction)`."),
              ("tkinter", "Les fenêtres : des éléments (`ttk.Button`, `tk.Canvas`) placés avec `pack` ou `grid` ; "
                          "`command=` et `bind(\"<Événement>\", fonction)` relient un clic à une méthode."),
              ("Thèmes", "Les couleurs sont nommées par leur rôle (`INK`, `TINT`, `RAIL`, `CARD_BG`…) et "
                         "choisies par `use_theme()` avant de construire les fenêtres.")]),
    ("h2", "Petit lexique pour lire une ligne", "lexique-ligne"),
    ("table", [["Écrit", "Se lit"],
               ["`a = b`", "a reçoit la valeur de b (ce n'est pas une égalité)"],
               ["`a == b`, `a != b`", "a est-il égal à b ? différent ?"],
               ["`a += 1`", "a augmente de 1"],
               ["`x ** 2`", "x au carré"],
               ["`if … :`, `elif … :`, `else:`", "si…, sinon si…, sinon"],
               ["`for x in liste:`", "pour chaque élément de la liste"],
               ["`# texte`", "un commentaire, pour le lecteur"],
               ["`lab[..., 0]`", "le canal 0 (L\\*) de tous les pixels"],
               ["`rgb[y0:y1, x0:x1]`", "un rectangle de l'image"],
               ["`self.nom`", "une donnée de l'objet (la fenêtre, l'échelle…)"],
               ["`None`", "« rien » : pas de valeur"]], [0.35, 0.65]),

    ("part", "3", "Des fonctions réelles, ligne par ligne", "Ces extraits sont lus dans le code au moment où le "
     "guide est produit : ce sont exactement les lignes du programme.", "lignes"),
    ("h2", "to_lab : passer en CIELAB", "to-lab"),
    ("annotated", "gerbil.py", "to_lab", [
        "Définit la fonction `to_lab`, qui reçoit `rgb`, une image en rouge-vert-bleu.",
        "La docstring : ce que fait la fonction et pourquoi.",
        "OpenCV convertit l'image en Lab ; `.astype(np.float32)` passe en nombres à virgule. OpenCV range chaque "
        "canal de 0 à 255.",
        "Le canal 0 (L\\*) est ramené à l'échelle habituelle 0–100.",
        "Les canaux 1 et 2 (a\\* et b\\*) sont recentrés autour de 0.",
        "Renvoie l'image en Lab."]),
    ("h2", "distance : à quel point un pixel diffère du fond", "distance"),
    ("annotated", "gerbil.py", "distance", [
        "Reçoit l'image en Lab, la couleur de référence (le modèle du fond) et le poids de la clarté (0,5).",
        "La docstring.",
        "Écart de clarté de chaque pixel au fond, multiplié par le poids : une ombre compte moins.",
        "Écart sur a\\* (vert–rouge).",
        "Écart sur b\\* (bleu–jaune).",
        "La distance : racine de la somme des carrés, pour tous les pixels à la fois."]),
    ("h2", "hysteresis : garder les régions nettes et leurs bords pâles", "hysteresis"),
    ("annotated", "gerbil.py", "hysteresis", [
        "Reçoit la carte des distances `d` et les deux seuils (8 et 18).",
        "La docstring.",
        "`weak` : les pixels au-dessus du seuil bas.",
        "OpenCV numérote les régions d'un seul tenant de `weak` ; `lab` donne le numéro de chaque pixel (une "
        "« étiquette », rien à voir avec les couleurs Lab).",
        "Une liste de `n` réponses « garder ? », toutes à non.",
        "Les régions qui contiennent un pixel au-dessus du seuil haut passent à oui.",
        "La région 0, le fond, n'est jamais gardée.",
        "Chaque pixel prend la réponse de sa région : le masque."]),
    ("h2", "parse_ratio : lire une échelle écrite « 1/3 »", "parse-ratio"),
    ("annotated", "gerbil_plates.py", "parse_ratio", [
        "Reçoit un texte : « 1/3 », « 1:3 » ou « 3 ».",
        "La docstring : « 2/3 » donne 1,5 (réduction aux deux tiers).",
        "Le texte est nettoyé ; une virgule décimale devient un point.",
        "Essayer ce qui suit ; en cas d'erreur, aller à `except`.",
        "Si le texte contient « / » ou « : »…",
        "… le couper en deux : `a` avant, `b` après…",
        "… et renvoyer b ÷ a (1/3 → 3).",
        "Sinon, renvoyer le nombre seul.",
        "Si la lecture échoue ou divise par zéro…",
        "… renvoyer `None` : l'interface garde l'ancienne valeur."]),
    ("h2", "Tooltip.__init__ : une bulle d'aide sur un bouton", "tooltip"),
    ("annotated", "gerbil_gui.pyw", "Tooltip.__init__", [
        "La méthode qui construit une bulle d'aide : `widget` est l'élément, `text` l'explication.",
        "La docstring.",
        "Garde l'élément et le texte ; la bulle et la tâche prévue n'existent pas encore.",
        "Quand la souris **entre** : prévoir l'affichage (450 ms) ; `add=\"+\"` garde les autres liens.",
        "Quand la souris **sort** : cacher la bulle.",
        "Au **clic** : la cacher.",
        "Quand l'élément perd le **focus** : la cacher.",
        "Quand l'élément est **détruit** : la cacher."]),

    ("part", "4", "Modifier le code sans rien casser", "Les règles de la maison, les tests, et comment refaire "
     "les guides.", "modifier"),
    ("h2", "Les règles", "regles"),
    ("ul", ["Noms et messages en anglais ; constantes en majuscules en haut de leur section, avec un commentaire.",
            "Les commentaires disent *pourquoi* ; les docstrings disent *quoi* et, brièvement, *comment*.",
            "**Un changement doit laisser identiques, au pixel près, les résultats déjà justes** : on le vérifie "
            "sur les lots de référence avant de l'adopter (`CONTRIBUTING.md`).",
            "Les noms des fichiers produits ne changent pas sans raison : d'autres outils les lisent.",
            "Les fichiers `.bat` restent en fins de ligne Windows (CRLF)."]),
    ("h2", "Tests et guides", "tests-guides"),
    ("code", "py -3 -m pytest tests                    les tests automatiques (photos synthétiques)\n"
             "py -3 docs/make_code_guide.py            docs/CODE_GUIDE.md\n"
             "py -3 docs/make_guide_shots.py           les captures de l'interface (il faut un écran)\n"
             "py -3 docs/make_guide_pdf.py             les quatre guides PDF (Edge ou Chrome)"),
    ("p", "Une fonction nouvelle sans explication française apparaît dans la référence avec son explication "
          "anglaise, marquée « à traduire » : l'ajouter dans `docs/fr/reference_fr_more.py`."),
]
