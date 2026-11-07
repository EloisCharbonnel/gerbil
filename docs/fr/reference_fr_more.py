"""Explications en français (suite) : interface, planches, outils, installateur, tests.
Même clé que reference_fr.py : "fichier:Classe.fonction"."""

FR = {
    # ======================================================================== gerbil_gui.pyw
    "gerbil_gui.pyw:__module__": "L'interface graphique de Gerbil. On choisit les photos (dossiers ou fichiers) et "
        "les options, puis « Run » : le moteur tourne en arrière-plan et chaque photo traitée s'affiche dans le "
        "journal. Les paquets Python manquants (numpy, OpenCV, Pillow, rawpy) sont détectés et peuvent être "
        "installés depuis la fenêtre ; en console : py -3 gerbil_gui.pyw --install (ou --check).",
    "gerbil_gui.pyw:open_photo_image": "La photo redressée, telle que le moteur la voit (un RAW est développé de la "
        "même façon ; « small » : demi-taille, pour les aperçus). Renvoie une image PIL en RVB.",
    "gerbil_gui.pyw:python_exe": "Le Python « console » de l'installation (l'interface peut tourner sous pythonw, "
        "sans console).",
    "gerbil_gui.pyw:missing_packages": "Les paquets Python encore à installer (aucun dans la version .exe, qui "
        "contient tout).",
    "gerbil_gui.pyw:has_ai": "Vrai quand onnxruntime (le moteur de l'IA) est disponible.",
    "gerbil_gui.pyw:pip_command": "La commande pip qui installe des paquets pour le Python trouvé.",
    "gerbil_gui.pyw:imports_ok": "Vérifie les imports dans un nouveau processus : un paquet tout juste installé y "
        "est visible.",
    "gerbil_gui.pyw:console_install": "Install.bat : installe ce qui manque, dans le Python qui exécute ce fichier.",
    "gerbil_gui.pyw:count_photos": "Le nombre de photos (extensions connues) d'un dossier.",
    "gerbil_gui.pyw:load_settings": "Les réglages de l'interface (~/.gerbil.json, ou les fichiers des anciens noms), "
        "complétés par les valeurs par défaut.",
    "gerbil_gui.pyw:Tooltip": "La bulle d'aide qui apparaît quand la souris reste sur un élément. Elle disparaît "
        "quand la souris s'en va (vérifié toutes les 250 ms, car une liste déroulante ou une fenêtre ouverte "
        "entre-temps peut « avaler » l'événement de sortie), à un clic, et au bout de 8 s ; une seule bulle à "
        "la fois.",
    "gerbil_gui.pyw:Tooltip.__init__": "Attache la bulle à l'élément : montrée quand la souris s'y arrête, cachée à "
        "la sortie, au clic, à la perte du focus ou à la destruction.",
    "gerbil_gui.pyw:Tooltip._schedule": "La souris entre : la bulle sera montrée dans 450 ms.",
    "gerbil_gui.pyw:Tooltip._pointer_inside": "Vrai quand le pointeur est sur l'élément (ou l'un de ses enfants).",
    "gerbil_gui.pyw:Tooltip._show": "Montre la bulle sous l'élément, si la souris y est encore ; une seule bulle à "
        "la fois.",
    "gerbil_gui.pyw:Tooltip._watch": "Toutes les 250 ms : cache la bulle si la souris est partie, ou après 8 s.",
    "gerbil_gui.pyw:Tooltip._hide": "Cache la bulle et annule ce qui était prévu.",
    "gerbil_gui.pyw:ScaleWindow": "L'échelle à la main pour une photo : deux points de distance connue, cliqués sur "
        "la photo (redressée comme le moteur la voit). Enregistrée dans gerbil_scales.json à côté de la photo ; "
        "le moteur l'utilise alors au lieu de chercher l'échelle.",
    "gerbil_gui.pyw:ScaleWindow.__init__": "Construit la fenêtre. seq : série de photos corrigées l'une après l'autre "
        "(voir App.scale_series) ; on_saved : appelé après l'enregistrement (fenêtre de vérification) ; learn : "
        "reçoit les deux points au lieu d'enregistrer une échelle manuelle (profil de site : apprendre une "
        "échelle).",
    "gerbil_gui.pyw:ScaleWindow.fit": "La photo entière dans la fenêtre.",
    "gerbil_gui.pyw:ScaleWindow.to_screen": "Pixel de la photo → position dans la fenêtre (zoom et décalage de la vue).",
    "gerbil_gui.pyw:ScaleWindow.to_image": "Position dans la fenêtre → pixel de la photo.",
    "gerbil_gui.pyw:ScaleWindow.redraw": "Dessine la partie visible de la photo, les deux points, le segment et la "
        "bande de l'échelle.",
    "gerbil_gui.pyw:ScaleWindow.values": "(px/cm, largeur en cm) d'après les deux points et les champs ; px/cm vide "
        "quand il ne peut pas être calculé.",
    "gerbil_gui.pyw:ScaleWindow.update_readout": "Le texte sous les champs : distance en pixels, px/cm et ppp (ppi).",
    "gerbil_gui.pyw:ScaleWindow.press": "Clic : attrape un point proche, ou place un nouveau point.",
    "gerbil_gui.pyw:ScaleWindow.move": "Glisser : déplace le point attrapé.",
    "gerbil_gui.pyw:ScaleWindow.pan_move": "Bouton droit maintenu : déplace la vue.",
    "gerbil_gui.pyw:ScaleWindow.wheel": "Molette : zoom sur le point sous la souris.",
    "gerbil_gui.pyw:ScaleWindow._load": "Les échelles manuelles du dossier (gerbil_scales.json).",
    "gerbil_gui.pyw:ScaleWindow._write": "Écrit les échelles manuelles (à côté, puis échangé) ; le fichier de l'ancien "
        "nom est supprimé.",
    "gerbil_gui.pyw:ScaleWindow.save": "Enregistre l'échelle de la photo (ou la donne au profil en mode "
        "apprentissage), puis photo suivante de la série, ou propose de retraiter la photo.",
    "gerbil_gui.pyw:ScaleWindow.skip": "Série : laisse cette photo sans échelle et passe à la suivante.",
    "gerbil_gui.pyw:ScaleWindow.close": "Fermer (une photo) ou Arrêter (série : les photos déjà réglées peuvent alors "
        "être traitées).",
    "gerbil_gui.pyw:ScaleWindow.remove": "Supprime l'échelle manuelle de la photo (la détection est de nouveau "
        "utilisée).",
    "gerbil_gui.pyw:load_project_file": "Le projet d'un dossier (dictionnaire), un nouveau s'il n'y en a pas ; None si "
        "le fichier est illisible.",
    "gerbil_gui.pyw:save_project_file": "Écrit gerbil_project.json (écrit à côté puis échangé : jamais à moitié "
        "écrit).",
    "gerbil_gui.pyw:project_values": "Les valeurs d'une photo : celles communes, remplacées par les siennes.",
    "gerbil_gui.pyw:project_output_name": "Le nom de sortie d'une photo (comme project_name du moteur), ou son propre "
        "nom s'il n'y a pas de modèle.",
    "gerbil_gui.pyw:rule_regex": "La règle de nommage telle que -match de PowerShell la lit : expression régulière "
        ".NET, sans distinction de casse, trouvée n'importe où dans le nom sauf ancrée par ^ et $. Les groupes "
        "nommés .NET (?<nom>…) sont acceptés, et (?-i) au début rend la règle sensible à la casse.",
    "gerbil_gui.pyw:ps_escape": "Un texte pris littéralement dans une expression régulière .NET / PowerShell (comme "
        "[regex]::Escape).",
    "gerbil_gui.pyw:build_rule": "Construit une règle PowerShell faite de « regards en avant » (chacun teste le nom "
        "entier), par exemple (?-i)^(?!.*[a-z])(?=QSR25)(?=.{1,40}$) ; sensible à la casse quand un morceau "
        "l'exige.",
    "gerbil_gui.pyw:read_table": "Les lignes (listes de textes) d'un CSV ou de la première feuille d'un fichier Excel "
        ".xlsx.",
    "gerbil_gui.pyw:FieldDialog": "Ajoute ou modifie un champ du projet : libellé, clé (nom utilisé dans le modèle), "
        "obligatoire, choix possibles.",
    "gerbil_gui.pyw:FieldDialog.__init__": "La petite fenêtre de création ou de modification d'un champ.",
    "gerbil_gui.pyw:FieldDialog.ok": "Vérifie et renvoie le champ (clé faite de lettres, chiffres et _).",
    "gerbil_gui.pyw:ProjectWindow": "Le projet d'un dossier de photos (gerbil_project.json à côté d'elles) : champs, "
        "modèle de nom, règle de nommage, valeurs communes, et un tableau d'une ligne par photo (double-clic pour "
        "modifier une case ; plusieurs lignes sélectionnées : « Set for selected », « Number the selected ») ; "
        "import d'un inventaire CSV / Excel. Les fichiers produits prennent les noms construits avec le modèle "
        "(les photos gardent les leurs).",
    "gerbil_gui.pyw:ProjectWindow.__init__": "La fenêtre du renommage en lot : champs, modèle, règle et son assistant, "
        "valeurs communes, tableau des photos avec aperçu, boutons.",
    "gerbil_gui.pyw:ProjectWindow.fields": "Les champs du projet.",
    "gerbil_gui.pyw:ProjectWindow.rebuild": "Les champs ont changé : jetons, valeurs communes et colonnes du tableau "
        "redessinés.",
    "gerbil_gui.pyw:ProjectWindow.fill": "Remplit le tableau : une ligne par photo, ses valeurs et son nom de sortie.",
    "gerbil_gui.pyw:ProjectWindow.update_preview": "Exemple de nom de sortie, et avertissement quand un nom est utilisé "
        "deux fois.",
    "gerbil_gui.pyw:ProjectWindow.changes": "Le modèle a changé : noms de sortie recalculés.",
    "gerbil_gui.pyw:ProjectWindow.set_common": "Donne une valeur commune à toutes les photos.",
    "gerbil_gui.pyw:ProjectWindow.headings": "Les titres des colonnes ; une valeur commune est écrite dans le titre "
        "(les cases contiennent les valeurs propres à chaque photo, qui la remplacent).",
    "gerbil_gui.pyw:ProjectWindow.set_value": "Donne la valeur d'un champ pour une photo (tableau et projet).",
    "gerbil_gui.pyw:ProjectWindow.ext_changed": "« Extension in lowercase » coché ou non.",
    "gerbil_gui.pyw:ProjectWindow.ext_feedback": "Le nombre de photos dont l'extension a des majuscules.",
    "gerbil_gui.pyw:ProjectWindow.helper_changed": "Morceaux cochés → règle écrite dans le champ de la règle (qui reste "
        "modifiable à la main).",
    "gerbil_gui.pyw:ProjectWindow.rule_feedback": "La règle en ligne PowerShell, et le résultat pour le nom à tester "
        "(ou le premier nom de sortie).",
    "gerbil_gui.pyw:ProjectWindow.show_thumb": "Petite vue de la photo de la ligne sélectionnée (la première).",
    "gerbil_gui.pyw:ProjectWindow.render_thumb": "L'aperçu ajusté à la place disponible (il suit la barre entre "
        "tableau et aperçu).",
    "gerbil_gui.pyw:ProjectWindow.after_resize": "Aperçu redessiné un instant après le redimensionnement de la "
        "fenêtre.",
    "gerbil_gui.pyw:ProjectWindow.open_photo": "Ouvre la photo sélectionnée dans la visionneuse de Windows.",
    "gerbil_gui.pyw:ProjectWindow.select_all": "Sélectionne toutes les lignes (Ctrl+A).",
    "gerbil_gui.pyw:ProjectWindow.cell_clicked": "Clic dans le tableau : la case devient la case active (poignée de "
        "recopie).",
    "gerbil_gui.pyw:ProjectWindow.place_handle": "Le petit carré au coin inférieur droit de la case active (poignée de "
        "recopie, comme dans Excel).",
    "gerbil_gui.pyw:ProjectWindow.fill_start": "La poignée de recopie est saisie (Ctrl : numérotation).",
    "gerbil_gui.pyw:ProjectWindow.fill_move": "Glisser la poignée : lignes couvertes, tableau défilant à ses bords.",
    "gerbil_gui.pyw:ProjectWindow.fill_end": "Poignée relâchée : la valeur est recopiée (ou numérotée) dans les lignes "
        "couvertes.",
    "gerbil_gui.pyw:ProjectWindow.fill_down": "Ctrl+D : les valeurs de la première ligne sélectionnée recopiées dans "
        "les autres (seulement la colonne active si une case est active, sinon tous les champs).",
    "gerbil_gui.pyw:ProjectWindow.edit_cell": "Double-clic : modifie la case sur place (champ de saisie ou liste de "
        "choix).",
    "gerbil_gui.pyw:ProjectWindow._ask_field": "Petite boîte de dialogue : un champ et une valeur (ou un nombre de "
        "départ et un pas).",
    "gerbil_gui.pyw:ProjectWindow.set_selected": "Même valeur pour les photos sélectionnées.",
    "gerbil_gui.pyw:ProjectWindow.number_selected": "Numérote les photos sélectionnées (départ, pas, zéros).",
    "gerbil_gui.pyw:ProjectWindow.add_field": "Ajoute un champ.",
    "gerbil_gui.pyw:ProjectWindow._pick_field": "Demande sur quel champ agir.",
    "gerbil_gui.pyw:ProjectWindow.edit_field": "Modifie un champ (ses valeurs suivent un changement de clé).",
    "gerbil_gui.pyw:ProjectWindow.remove_field": "Supprime un champ et ses valeurs.",
    "gerbil_gui.pyw:ProjectWindow.import_table": "Importe les valeurs d'un inventaire CSV ou Excel : lignes associées "
        "aux photos par leur nom, colonnes associées aux champs.",
    "gerbil_gui.pyw:ProjectWindow.save": "Vérifie la règle et enregistre gerbil_project.json (puis lance le "
        "traitement, si demandé).",
    "gerbil_gui.pyw:ProjectWindow.close": "Ferme, en proposant d'enregistrer les changements.",
    "gerbil_gui.pyw:ReviewWindow": "La vérification et la correction des détourages, photo par photo (les douteuses "
        "d'abord) : la photo avec le contour du détourage (vert) et de l'échelle (magenta) ; pinceaux effacer / "
        "ajouter, suppression d'un morceau entier d'un clic, annulation ; orientation de l'objet (un trait le "
        "long du bord, ou des quarts de tour) ; accès à l'échelle manuelle. Les corrections sont enregistrées à "
        "côté des photos (gerbil_edits) pour qu'un traitement suivant les garde ; les photos corrigées sont "
        "ensuite retraitées.",
    "gerbil_gui.pyw:ReviewWindow.__init__": "La fenêtre de vérification : liste des photos, vue, outils, orientation, "
        "informations, boutons ; raccourcis clavier et souris.",
    "gerbil_gui.pyw:ReviewWindow.goto": "Affiche la photo n° i : son détourage (ou les corrections déjà "
        "enregistrées), son angle, ses informations ; remet l'historique d'annulation à zéro.",
    "gerbil_gui.pyw:ReviewWindow.show_info": "Les champs du projet de la photo, avec ses propres valeurs (les valeurs "
        "communes sont données en indication).",
    "gerbil_gui.pyw:ReviewWindow.save_info": "Enregistre dans son projet les informations saisies pour la photo "
        "affichée ; vrai si quelque chose a changé.",
    "gerbil_gui.pyw:ReviewWindow.fit": "La photo entière dans la vue. Refait une fois que la fenêtre a sa vraie "
        "taille (à l'ouverture la zone de dessin fait encore 1 × 1 pixel : la première photo resterait "
        "invisible).",
    "gerbil_gui.pyw:ReviewWindow.to_screen": "Pixel de la photo → position dans la fenêtre.",
    "gerbil_gui.pyw:ReviewWindow.to_image": "Position dans la fenêtre → pixel de la photo.",
    "gerbil_gui.pyw:ReviewWindow.view_base": "La photo telle qu'affichée pour la vue actuelle (gardée en mémoire : "
        "refaite seulement quand la vue change).",
    "gerbil_gui.pyw:ReviewWindow.redraw": "Photo (en mémoire) + détourage (fond assombri, contour vert) + contour de "
        "l'échelle + trait ou lasso en cours.",
    "gerbil_gui.pyw:ReviewWindow.schedule_redraw": "Au plus un rafraîchissement toutes les 30 ms pendant qu'on peint "
        "(le masque lui-même est modifié tout de suite).",
    "gerbil_gui.pyw:ReviewWindow.wheel": "Molette : zoom sur le point sous la souris.",
    "gerbil_gui.pyw:ReviewWindow.pan_move": "Déplace la vue tant qu'un bouton est maintenu.",
    "gerbil_gui.pyw:ReviewWindow.view_span": "La partie visible de la photo sur un axe : (début, longueur) en pixels "
        "de la photo.",
    "gerbil_gui.pyw:ReviewWindow.scroll_view": "Les commandes des barres de défilement : « moveto f » ou « scroll n "
        "units|pages ».",
    "gerbil_gui.pyw:ReviewWindow.nudge": "Flèches du clavier : déplacent la vue.",
    "gerbil_gui.pyw:ReviewWindow.update_bars": "Barres de défilement ajustées à la partie visible de la photo.",
    "gerbil_gui.pyw:ReviewWindow.hover": "Le cercle du pinceau sous la souris.",
    "gerbil_gui.pyw:ReviewWindow.tool_changed": "Un outil est choisi : le modèle « un clic » est préparé quand c'est "
        "lui.",
    "gerbil_gui.pyw:ReviewWindow.prepare_click": "Charge le modèle (téléchargé une fois, 45 Mo) et encode la photo "
        "affichée, en arrière-plan.",
    "gerbil_gui.pyw:ReviewWindow.click_prepared": "La photo est prête pour le « un clic » (ou l'erreur est affichée).",
    "gerbil_gui.pyw:ReviewWindow.show_click_hint": "Comment utiliser l'outil « un clic ».",
    "gerbil_gui.pyw:ReviewWindow.click_object": "Un clic : l'objet sous le clic (Segment Anything, avec le bord du "
        "détourage calculé là où ils sont d'accord) est ajouté (ou retiré avec Maj).",
    "gerbil_gui.pyw:ReviewWindow._save_patch": "Garde la partie du masque qui va changer, pour l'annulation (30 "
        "étapes).",
    "gerbil_gui.pyw:ReviewWindow.typing": "Un champ de texte du panneau a le clavier : l'espace et les flèches sont "
        "pour lui.",
    "gerbil_gui.pyw:ReviewWindow.press": "Bouton de la souris enfoncé : commence le pinceau, le lasso, le trait, ou "
        "agit tout de suite (morceau, un clic) ; espace maintenue : déplace la vue.",
    "gerbil_gui.pyw:ReviewWindow.drag": "Souris déplacée bouton enfoncé : peint, prolonge le lasso ou le trait.",
    "gerbil_gui.pyw:ReviewWindow._paint": "Peint (ou efface) un coup de pinceau dans le masque.",
    "gerbil_gui.pyw:ReviewWindow.release": "Bouton relâché : termine le coup de pinceau, remplit le lasso, ou tourne "
        "l'objet selon le trait tracé.",
    "gerbil_gui.pyw:ReviewWindow.rim_angle": "La rotation (en degrés, sens inverse des aiguilles d'une montre) qui rend "
        "le trait horizontal avec l'objet en dessous.",
    "gerbil_gui.pyw:ReviewWindow.turn": "Quart de tour de l'objet (ou retour à 0).",
    "gerbil_gui.pyw:ReviewWindow.undo": "Annule la dernière modification du masque ou de l'angle.",
    "gerbil_gui.pyw:ReviewWindow.reset": "Annule toutes les modifications non enregistrées de cette photo ; si des "
        "corrections avaient été enregistrées, propose de les supprimer aussi (le détourage calculé revient au "
        "prochain traitement).",
    "gerbil_gui.pyw:ReviewWindow.remove_saved": "Supprime les corrections enregistrées pour une photo.",
    "gerbil_gui.pyw:ReviewWindow.update_thumb": "L'objet tel qu'il sera exporté (tourné), en petit.",
    "gerbil_gui.pyw:ReviewWindow.list_text": "Le texte d'une photo dans la liste : marque d'état, nom, état de "
        "l'export.",
    "gerbil_gui.pyw:ReviewWindow.mark": "Change l'état d'export affiché pour une photo.",
    "gerbil_gui.pyw:ReviewWindow.saved_mask_file": "Le chemin du masque corrigé d'une photo (gerbil_edits).",
    "gerbil_gui.pyw:ReviewWindow.saved_entry": "Les corrections enregistrées pour une photo (masque corrigé ? angle).",
    "gerbil_gui.pyw:ReviewWindow.export": "La photo est retraitée en arrière-plan dès que ses corrections sont "
        "enregistrées : résultats et aperçus sont à jour sans repasser par toutes les photos.",
    "gerbil_gui.pyw:ReviewWindow.pump": "Lance les exports en attente dès que la fenêtre principale est libre (un "
        "traitement à la fois, toutes les photos en attente ensemble).",
    "gerbil_gui.pyw:ReviewWindow.save_current": "Enregistre les corrections de la photo affichée (gerbil_edits à côté "
        "de la photo) ; vrai si quelque chose a changé.",
    "gerbil_gui.pyw:ReviewWindow.accept": "Enregistre les corrections de la photo, la réexporte, affiche la suivante.",
    "gerbil_gui.pyw:ReviewWindow.fix_scale": "Ouvre l'échelle manuelle de la photo.",
    "gerbil_gui.pyw:ReviewWindow.close": "Ferme, en proposant de garder les corrections de la photo affichée.",
    "gerbil_gui.pyw:PlatesWindow": "Les planches d'un dossier de résultats (gerbil_plates) : objets à une échelle "
        "choisie sur des pages, légendes, barre d'échelle graphique à la manière de QGIS ; aperçu en direct des "
        "pages ; écrites en SVG (Illustrator, Inkscape). Les réglages sont gardés (style maison de la barre "
        "d'échelle).",
    "gerbil_gui.pyw:PlatesWindow.__init__": "La fenêtre des planches : trois onglets de réglages (planche, barre "
        "d'échelle, échelles et dessins), aperçu en direct avec zoom, boutons.",
    "gerbil_gui.pyw:PlatesWindow.object_scales": "Petite fenêtre : chaque objet avec sa taille et son échelle (celle "
        "de la planche, ou une choisie pour lui).",
    "gerbil_gui.pyw:PlatesWindow.wheel": "Zoom sur le point sous la souris (1 = page entière, jusqu'à 8).",
    "gerbil_gui.pyw:PlatesWindow.object_menu": "Clic droit sur un objet de l'aperçu : un menu d'échelles pour lui "
        "(gardé dans les réglages de la planche).",
    "gerbil_gui.pyw:PlatesWindow.pick_drawings": "Choisit le dossier des dessins.",
    "gerbil_gui.pyw:PlatesWindow.colour_button": "Une pastille de couleur qui ouvre le sélecteur de couleur.",
    "gerbil_gui.pyw:PlatesWindow.settings": "Les PlateSettings lus dans la fenêtre (un nombre invalide garde sa valeur "
        "précédente).",
    "gerbil_gui.pyw:PlatesWindow.changed": "Un réglage a changé : l'aperçu est redessiné un instant plus tard.",
    "gerbil_gui.pyw:PlatesWindow.thumb": "L'image réduite d'un objet pour l'aperçu (gardée en mémoire).",
    "gerbil_gui.pyw:PlatesWindow.refresh": "Met en page les planches avec les réglages actuels et dessine la page "
        "affichée.",
    "gerbil_gui.pyw:PlatesWindow.turn": "Planche précédente / suivante.",
    "gerbil_gui.pyw:PlatesWindow.write": "Écrit les planches SVG dans un fil d'exécution séparé.",
    "gerbil_gui.pyw:PlatesWindow.written": "Planches écrites : message, réglages enregistrés.",
    "gerbil_gui.pyw:PlatesWindow.open_folder": "Ouvre le dossier des planches.",
    "gerbil_gui.pyw:PlatesWindow.close": "Ferme, en enregistrant les réglages (style maison).",
    "gerbil_gui.pyw:profile_names": "Les noms des profils de site de la bibliothèque.",
    "gerbil_gui.pyw:profile_path": "Le fichier d'un profil de la bibliothèque.",
    "gerbil_gui.pyw:safe_name": "Un nom utilisable comme nom de fichier Windows.",
    "gerbil_gui.pyw:ProfileWindow": "Le profil de site : ce que l'on sait des photos d'un site ou d'une campagne (fond, "
        "échelles apprises, options), choisi une fois dans la fenêtre principale au lieu de tout régler de "
        "nouveau. Enregistré dans la bibliothèque des profils ; « Put next to the photos… » le copie en "
        "gerbil_profile.json dans un dossier de photos, où le moteur l'utilise tout seul (et l'équipe peut le "
        "partager).",
    "gerbil_gui.pyw:ProfileWindow.__init__": "La fenêtre du profil : nom, fond, échelles apprises, options.",
    "gerbil_gui.pyw:ProfileWindow.fill": "La liste des échelles apprises et le résumé des options gardées.",
    "gerbil_gui.pyw:ProfileWindow.learn": "Choisir une photo montrant l'échelle et ouvrir la fenêtre de l'échelle en "
        "mode apprentissage.",
    "gerbil_gui.pyw:ProfileWindow.learned": "Apprend l'échelle à partir des deux points donnés (learn_scale du "
        "moteur).",
    "gerbil_gui.pyw:ProfileWindow.remove_scale": "Supprime une échelle apprise.",
    "gerbil_gui.pyw:ProfileWindow.take_options": "Garde dans le profil les options de la fenêtre principale.",
    "gerbil_gui.pyw:ProfileWindow.data": "Le profil tel qu'il est enregistré.",
    "gerbil_gui.pyw:ProfileWindow.save": "Enregistre le profil dans la bibliothèque et le choisit.",
    "gerbil_gui.pyw:ProfileWindow.export": "Écrit le profil en gerbil_profile.json dans un dossier de photos.",
    "gerbil_gui.pyw:IptcWindow": "Les champs IPTC du renommage en lot : pour chaque champ IPTC Core, un texte où "
        "{champ} est remplacé par la valeur de la photo et {name} par le nom de sortie (un texte sans accolades "
        "est le même pour toutes, par exemple le copyright). Inscrits dans le PSD / TIFF, la copie de l'original "
        "et, si coché, un fichier .xmp à côté de chaque photo originale.",
    "gerbil_gui.pyw:IptcWindow.__init__": "La fenêtre IPTC : un texte par champ IPTC, option du .xmp, exemple.",
    "gerbil_gui.pyw:IptcWindow.mapping": "Les champs IPTC remplis.",
    "gerbil_gui.pyw:IptcWindow.preview": "Exemple des valeurs IPTC de la photo sélectionnée.",
    "gerbil_gui.pyw:IptcWindow.default": "Le modèle par défaut.",
    "gerbil_gui.pyw:IptcWindow.ok": "Garde les réglages IPTC dans le projet.",
    "gerbil_gui.pyw:InventoryWindow": "L'inventaire de dossiers de documentation en CSV (inventory de gerbil_tools), "
        "avec la ligne PowerShell qui fait la même chose, affichée pour apprendre.",
    "gerbil_gui.pyw:InventoryWindow.__init__": "La fenêtre de l'inventaire : dossiers, types de fichiers, champs des "
        "noms, ligne PowerShell.",
    "gerbil_gui.pyw:InventoryWindow.add": "Ajoute un dossier.",
    "gerbil_gui.pyw:InventoryWindow.chosen": "Les dossiers et types de fichiers choisis.",
    "gerbil_gui.pyw:InventoryWindow.out_path": "Le chemin par défaut du CSV.",
    "gerbil_gui.pyw:InventoryWindow.update_line": "Met à jour la ligne PowerShell.",
    "gerbil_gui.pyw:InventoryWindow.write": "Écrit l'inventaire et l'ouvre.",
    "gerbil_gui.pyw:ThumbnailsWindow": "Les vignettes en lot (thumbnails de gerbil_tools), pour les bases de données.",
    "gerbil_gui.pyw:ThumbnailsWindow.__init__": "La fenêtre des vignettes : dossier, taille, format.",
    "gerbil_gui.pyw:ThumbnailsWindow.browse": "Choisit le dossier.",
    "gerbil_gui.pyw:ThumbnailsWindow.run": "Fabrique les vignettes dans un fil d'exécution séparé.",
    "gerbil_gui.pyw:ThumbnailsWindow.done": "Vignettes faites : message, dossier ouvert.",
    "gerbil_gui.pyw:App": "La fenêtre principale : liste des photos, options, Run, journal ; elle lance le moteur et "
        "ouvre les autres fenêtres (renommage en lot, échelle, vérification, planches, profils, outils).",
    "gerbil_gui.pyw:App.__init__": "La fenêtre principale : réglages, styles, éléments, vérification des paquets.",
    "gerbil_gui.pyw:App._icon": "La gerbille violette : icône de la fenêtre et image de l'en-tête (taille selon la mise "
        "à l'échelle de l'écran).",
    "gerbil_gui.pyw:App._style": "Couleurs et polices des éléments (styles ttk).",
    "gerbil_gui.pyw:App._build": "Construit la fenêtre principale : en-tête, photos, options, Run, journal.",
    "gerbil_gui.pyw:App._photos_card": "La carte des photos : boutons, liste, dossier de résultats, profil de site.",
    "gerbil_gui.pyw:App.apply_profile": "Les options gardées dans le profil choisi sont reportées dans la fenêtre.",
    "gerbil_gui.pyw:App.profiles_changed": "Liste des profils mise à jour, le profil enregistré choisi.",
    "gerbil_gui.pyw:App._options_card": "La carte des options (fichiers, traitement, échelle et mise en page, "
        "nettoyage, IA).",
    "gerbil_gui.pyw:App._ai_ticked": "IA cochée : propose d'installer onnxruntime s'il manque.",
    "gerbil_gui.pyw:App.check_packages": "Bandeau et bouton Run selon les paquets nécessaires.",
    "gerbil_gui.pyw:App.install_required": "Installe les paquets manquants (pip, en arrière-plan).",
    "gerbil_gui.pyw:App._sync": "Active les options qui dépendent d'une autre.",
    "gerbil_gui.pyw:App.add_paths": "Ajoute des dossiers / photos à la liste (avec leur nombre de photos).",
    "gerbil_gui.pyw:App.add_folder": "Ajoute un dossier de photos.",
    "gerbil_gui.pyw:App.add_files": "Ajoute des photos.",
    "gerbil_gui.pyw:App.project": "Le projet du dossier sélectionné dans la liste (ou du dossier de la photo "
        "sélectionnée).",
    "gerbil_gui.pyw:App.set_scale": "L'échelle manuelle d'une photo : celle sélectionnée dans la liste, sinon une à "
        "choisir.",
    "gerbil_gui.pyw:App.scale_series": "Les échelles manuelles de plusieurs photos, une fenêtre après l'autre ; les "
        "photos dont l'échelle a été enregistrée peuvent ensuite être retraitées en une fois.",
    "gerbil_gui.pyw:App.next_scale": "Série d'échelles manuelles : ouvre la photo suivante.",
    "gerbil_gui.pyw:App.remove": "Retire les lignes sélectionnées de la liste.",
    "gerbil_gui.pyw:App.clear": "Vide la liste.",
    "gerbil_gui.pyw:App.pick_output": "Choisit le dossier de résultats (pas un dossier de photos).",
    "gerbil_gui.pyw:App._collect": "Lit les options ; renvoie les arguments de la ligne de commande (seulement ce qui "
        "diffère des valeurs par défaut).",
    "gerbil_gui.pyw:App.save_settings": "Enregistre les réglages de l'interface.",
    "gerbil_gui.pyw:App.run": "Traite les photos de la liste (ou celles données : une photo dont l'échelle vient "
        "d'être réglée, des photos corrigées dans la vérification). quiet : pas de question à la fin (exports de "
        "la vérification).",
    "gerbil_gui.pyw:App._start": "Lance le moteur (« script ») ou pip (« pip » : paquets nécessaires, « pip-ai » : "
        "onnxruntime).",
    "gerbil_gui.pyw:App._stop_bar": "Arrête la barre de progression animée.",
    "gerbil_gui.pyw:App._reader": "Fil d'exécution qui lit la sortie du moteur ligne par ligne (dans une file "
        "d'attente).",
    "gerbil_gui.pyw:App._poll": "Toutes les 100 ms : traite les lignes reçues ; détecte la fin du processus.",
    "gerbil_gui.pyw:App._handle": "Une ligne du moteur : progression, journal en couleur, dossier de résultats, "
        "photos dont l'échelle est à régler à la main.",
    "gerbil_gui.pyw:App._summary": "« 12 ok, 3 to verify, 1 failed ».",
    "gerbil_gui.pyw:App._finished": "Fin d'un traitement : état, propositions (échelles manuelles), fichier "
        "d'autotest.",
    "gerbil_gui.pyw:App.cancel": "Arrête le traitement (tout l'arbre de processus).",
    "gerbil_gui.pyw:App.review": "La fenêtre de vérification sur les dossiers de résultats du dernier traitement (ou "
        "un dossier de résultats à choisir).",
    "gerbil_gui.pyw:App.plates": "La fenêtre des planches sur un dossier de résultats (le dernier traité, ou un à "
        "choisir).",
    "gerbil_gui.pyw:App.open_results": "Ouvre les dossiers de résultats.",
    "gerbil_gui.pyw:App.help": "Ouvre le README.",
    "gerbil_gui.pyw:App.close": "Ferme (en arrêtant d'abord un traitement, si on le veut) et enregistre les réglages.",
    "gerbil_gui.pyw:App._log": "Ajoute un texte au journal, dans une couleur.",
    "gerbil_gui.pyw:App._clear_log": "Vide le journal.",
    "gerbil_gui.pyw:main": "Point d'entrée de l'interface : --install / --check pour Install.bat, --selftest, ou la "
        "fenêtre.",

    # ======================================================================== gerbil_plates.py
    "gerbil_plates.py:__module__": "Les planches : les objets détourés d'un dossier de résultats mis en page à une "
        "échelle choisie (1:1, 1:2, 1:3…), écrits en fichiers SVG qui s'ouvrent dans Illustrator ou Inkscape. "
        "Chaque objet garde sa vraie taille à l'échelle de la planche (lue dans la résolution de son "
        "_outlined.tif, qui est à 1:1). Les objets sont placés en rangées, dans l'ordre choisi, avec une légende "
        "sous chacun (son nom, ou les champs du renommage en lot) et une barre d'échelle graphique sur chaque "
        "page. Les images sont incluses : un fichier SVG peut être envoyé seul. La page est d'abord décrite comme "
        "une liste de formes en millimètres (Drawing), puis écrite en SVG ou dessinée avec Pillow pour l'aperçu : "
        "les deux montrent toujours la même chose. Usage : py -3 gerbil_plates.py DOSSIER_RESULTATS [--ratio 2] "
        "[--page A4] [--landscape] [-o DOSSIER].",
    "gerbil_plates.py:ScaleBar": "La barre d'échelle graphique, à la manière des mises en page de QGIS. Longueurs en "
        "centimètres réels, dimensions sur le papier en millimètres, textes en points.",
    "gerbil_plates.py:PlateSettings": "Tous les réglages des planches (page, échelle, légendes, titre, dessins, "
        "options) et la barre d'échelle ; enregistrés en JSON (réglages de l'interface, plates_settings.json).",
    "gerbil_plates.py:PlateSettings.from_dict": "Les réglages reconstruits à partir d'un dictionnaire (réglages "
        "enregistrés) ; les clés inconnues sont ignorées, pour que les anciens fichiers se chargent encore.",
    "gerbil_plates.py:PlateSettings.to_dict": "Les réglages en dictionnaire (pour les enregistrer en JSON).",
    "gerbil_plates.py:PlateSettings.page_size": "Largeur et hauteur de la page en mm, tournées en paysage.",
    "gerbil_plates.py:Item": "Un objet détouré d'un dossier de résultats : nom de sortie, fichier TIFF, taille réelle "
        "(cm), ligne du rapport, douteux ou non, cadre de l'objet dans le TIFF, dessin trouvé pour lui.",
    "gerbil_plates.py:natural_key": "Clé de tri où les nombres comptent comme des nombres : « 2 » avant « 10 ».",
    "gerbil_plates.py:read_report": "Les lignes de outlined_report.csv, par nom de sortie (champs des photos).",
    "gerbil_plates.py:collect": "Les objets détourés d'un dossier de résultats, avec leur taille réelle (d'après la "
        "résolution du TIFF).",
    "gerbil_plates.py:field_value": "La valeur d'une colonne du rapport pour l'objet : son nom exact, sinon les mêmes "
        "lettres et chiffres (casse, espaces et soulignés mis à part), sinon un champ du renommage qui se termine "
        "ainsi (« number » pour « Object number »).",
    "gerbil_plates.py:caption_text": "La légende d'un objet : le modèle avec {champ} remplacé par ses valeurs.",
    "gerbil_plates.py:report_fields": "Les champs utilisables pour l'ordre, les groupes et les légendes.",
    "gerbil_plates.py:Drawing": "Une page décrite comme des formes en millimètres, par calque : écrite en SVG "
        "(write_svg) ou dessinée avec Pillow pour l'aperçu (render), pour que les deux montrent toujours la "
        "même chose.",
    "gerbil_plates.py:Drawing.__init__": "Une page vide de largeur × hauteur mm.",
    "gerbil_plates.py:Drawing.add": "Ajoute une forme (un tuple : nature, coordonnées en mm, style) à un calque.",
    "gerbil_plates.py:pil_font": "Une police Pillow de la famille donnée, à une taille en pixels (gardée en mémoire), "
        "pour l'aperçu et pour mesurer les textes.",
    "gerbil_plates.py:text_width_mm": "La largeur d'un texte sur le papier (mesurée avec la police à 100 px par mm).",
    "gerbil_plates.py:svg_escape": "Protège un texte pour le SVG / XML.",
    "gerbil_plates.py:num": "Un nombre écrit court pour le SVG (3 décimales au plus, sans zéros de fin).",
    "gerbil_plates.py:write_svg": "Écrit un Drawing en fichier SVG en millimètres, un calque Inkscape / Illustrator par "
        "calque du dessin, les calques masqués masqués.",
    "gerbil_plates.py:svg_shape": "Une forme du dessin en SVG : rectangle, polygone / ligne, texte, texte vertical, "
        "image (PNG inclus en base64) ou dessin (SVG imbriqué).",
    "gerbil_plates.py:render": "La page en image Pillow (aperçu) ; les calques masqués seulement avec show_hidden.",
    "gerbil_plates.py:bar_geometry": "La longueur (cm réels) et les segments de la barre : donnés, ou choisis pour "
        "qu'elle reste sous max_mm.",
    "gerbil_plates.py:fmt": "Un nombre écrit sans décimales inutiles (3, 1,5).",
    "gerbil_plates.py:draw_bar": "Dessine la barre avec son coin supérieur gauche en (x0, y0), étiquettes comprises. "
        "Renvoie (largeur, hauteur).",
    "gerbil_plates.py:bar_size": "Largeur et hauteur d'une barre d'échelle, mesurées en la dessinant sur une page vide.",
    "gerbil_plates.py:inkscape": "La ligne de commande d'Inkscape, s'il est installé (il convertit .ai / .pdf / .eps "
        "et fait les aperçus).",
    "gerbil_plates.py:_cached": "Le chemin d'un fichier dans le cache des dessins, nommé d'après le chemin, la taille "
        "et la date de la source (un dessin modifié est de nouveau converti).",
    "gerbil_plates.py:drawing_svg": "Le SVG d'un dessin : le fichier lui-même, ou sa conversion par Inkscape (en "
        "cache). None si impossible.",
    "gerbil_plates.py:drawing_png": "L'image d'un dessin pour l'aperçu (Inkscape, en cache), ou None.",
    "gerbil_plates.py:_length_mm": "Une longueur SVG (« 12.5mm », « 300pt », « 800 ») en mm (pixels à 96 par pouce).",
    "gerbil_plates.py:svg_root": "(balise ouvrante de la racine <svg>, contenu) d'un document SVG.",
    "gerbil_plates.py:svg_size_mm": "Largeur et hauteur du dessin sur son papier (mm), d'après width / height de la "
        "racine (sinon viewBox à 96 px par pouce).",
    "gerbil_plates.py:norm": "Une valeur comparée sans casse, espaces, ponctuation ni zéros de tête (« 0187 » = "
        "« 187 »).",
    "gerbil_plates.py:attach_drawings": "Chaque objet reçoit le dessin du même objet trouvé dans le dossier des "
        "dessins : un dessin dont le nom (sans les suffixes de Gerbil) est le nom de sortie (modèle « {name} »), "
        "ou dont les champs, lus avec le modèle (par ex. {site}_{number}), sont ceux de l'objet (zéros de tête "
        "ignorés).",
    "gerbil_plates.py:Placed": "Un objet placé sur une planche : sa photo (x, y, l, h en mm), légende, échelle, cadre "
        "du dessin et cadre photo + dessin.",
    "gerbil_plates.py:sort_items": "Les objets triés par groupe, puis par le champ d'ordre, puis par nom.",
    "gerbil_plates.py:page_room": "La largeur et la hauteur (mm) qu'un objet et sa légende peuvent prendre sur une "
        "page avec ces réglages.",
    "gerbil_plates.py:parse_ratio": "« 1/3 », « 1:3 », « 3 » → 3 (planche au 1:3) ; « 2/3 » → 1,5.",
    "gerbil_plates.py:material_ratio": "L'échelle donnée par la matière de l'objet (material_ratios : « mot=1/3 ; … », "
        "le mot cherché dans la matière), ou None.",
    "gerbil_plates.py:object_mm": "La taille sur le papier d'un objet au 1:r (photo, et son dessin à côté) : "
        "(largeur, hauteur, largeur et hauteur de la photo, largeur et hauteur du dessin) en mm.",
    "gerbil_plates.py:object_ratio": "L'échelle d'un objet : celle choisie pour lui, sinon celle de sa matière "
        "(by_material), sinon celle de la planche ; et, quand il ne tient pas sur la page (fit_large), la première "
        "échelle usuelle à laquelle il tient.",
    "gerbil_plates.py:layout": "Les pages d'objets placés, une échelle par page : d'abord les objets à l'échelle de la "
        "planche, puis ceux réduits (trop grands, ou une échelle choisie pour eux), chaque échelle sur ses propres "
        "pages avec sa propre barre. Renvoie (pages, avertissements) ; une page est (groupe, [Placed], échelle).",
    "gerbil_plates.py:layout_one": "Les pages d'objets placés à une seule échelle (ou à celle que ratio_of donne à "
        "chacun, l'échelle étant alors écrite dans les légendes ; « bars » barres empilées en bas) : rangées "
        "remplies de gauche à droite, centrées, les images d'une rangée alignées sur leur bord inférieur, le "
        "dessin à côté de la photo, les légendes dessous. Renvoie (pages, avertissements).",
    "gerbil_plates.py:load_image": "L'image de l'objet à « dpi » sur le papier (jamais agrandie).",
    "gerbil_plates.py:page_drawing": "Le Drawing d'une page. images : True (fichiers lus au dpi de la planche), False "
        "(cadres gris) ou une fonction (objet, l_mm, h_mm) → image (l'interface donne ses vignettes en mémoire).",
    "gerbil_plates.py:draw_measures": "Largeur et hauteur de l'objet (cm réels, tel qu'il est posé sur la planche) en "
        "lignes de cote, au-dessus et à gauche, sur le calque masqué « Measurements » : des repères de mise en "
        "page, pas des données.",
    "gerbil_plates.py:plate_text": "Le titre ou le nom de fichier d'une planche : {page}, {pages}, {group} et {scale} "
        "remplacés (page sur 2 chiffres et échelle écrite 1-2 pour les fichiers, 1:2 dans un titre).",
    "gerbil_plates.py:plate_file_names": "Les noms de fichier des planches (sans dossier) : d'après le modèle, les "
        "caractères interdits dans un nom Windows remplacés par « _ » ; le numéro de page ajouté si le modèle "
        "n'en a pas.",
    "gerbil_plates.py:write_plates": "Écrit plate_01.svg, plate_02.svg… Renvoie (liste des fichiers, "
        "avertissements).",
    "gerbil_plates.py:main": "La ligne de commande des planches : options ou fichier de réglages, puis write_plates.",

    # ======================================================================== gerbil_tools.py
    "gerbil_tools.py:__module__": "Les outils : inventaire d'un dossier de documentation en CSV (photos, dessins, "
        "modèles 3D) et vignettes en lot pour les bases de données. Inventaire : une ligne par fichier, les "
        "colonnes choisies (fichier, dossier, type, taille, date, champs lus dans le nom avec un modèle comme "
        "{site}_{us}_{number}, taille de l'image, résolution, date de prise de vue, appareil) ; la ligne "
        "PowerShell qui fait la même chose (sans les informations d'image) est donnée aussi, pour apprendre. "
        "Vignettes : une copie réduite de chaque image (PNG avec transparence, ou JPEG sur blanc), la marge "
        "transparente des objets détourés coupée.",
    "gerbil_tools.py:kind_of": "Le type d'un fichier d'après son extension : photos, dessins, 3d, ou None.",
    "gerbil_tools.py:template_regex": "{site}_{us}_{number} → ^(?<site>.+?)_(?<us>.+?)_(?<number>.+?)$ (champs, texte "
        "fixe gardé). Renvoie (motif Python, motif PowerShell / .NET, noms des champs).",
    "gerbil_tools.py:list_files": "Les fichiers des types choisis dans les dossiers (sous-dossiers si on le veut, "
        "dossiers de travail de Gerbil exclus).",
    "gerbil_tools.py:image_info": "Taille, résolution, date de prise de vue et appareil d'une image (vides si elle "
        "est illisible).",
    "gerbil_tools.py:inventory": "Écrit l'inventaire ; renvoie (nombre de lignes, colonnes).",
    "gerbil_tools.py:ps_quote": "Un texte entre apostrophes pour PowerShell (apostrophes doublées).",
    "gerbil_tools.py:powershell_line": "Le même inventaire en PowerShell (colonnes du fichier et champs du nom ; pas "
        "d'informations d'image).",
    "gerbil_tools.py:thumbnails": "Écrit NOM_thumb.png / .jpg (plus grand côté = « size ») dans le dossier de sortie "
        "(par défaut un dossier « thumbnails » dans chaque dossier source). Renvoie la liste des fichiers écrits.",
    "gerbil_tools.py:main": "La ligne de commande : « inventory » ou « thumbnails ».",

    # ======================================================================== packaging/gerbil_setup.pyw
    "packaging/gerbil_setup.pyw:__module__": "L'installateur (Gerbil_Setup.exe, construit par build_exe.bat). Un seul "
        "fichier à envoyer : il contient toute la version .exe (Gerbil.zip) et l'installe pour l'utilisateur, "
        "sans droits d'administrateur : dans %LOCALAPPDATA%\\Programs\\Gerbil (ou un autre dossier), raccourcis "
        "dans le menu Démarrer et, si on veut, sur le bureau, entrée dans « Applications installées » de Windows "
        "(et Uninstall.bat dans le dossier) pour le désinstaller. Réinstaller par-dessus met à jour ; les modèles "
        "d'IA déjà téléchargés sont gardés. Les photos et les résultats ne sont jamais touchés.",
    "packaging/gerbil_setup.pyw:version": "La version de Gerbil, lue dans version.txt (inclus) ou dans gerbil.py.",
    "packaging/gerbil_setup.pyw:payload": "Le Gerbil.zip à installer (dans l'installateur, ou donné avec --zip pour "
        "les tests).",
    "packaging/gerbil_setup.pyw:running": "Les programmes Gerbil ouverts en ce moment.",
    "packaging/gerbil_setup.pyw:members": "Les fichiers de l'archive, sans le dossier « Gerbil » du haut : [(info, "
        "chemin relatif)].",
    "packaging/gerbil_setup.pyw:check_folder": "None si le dossier peut recevoir Gerbil, sinon la raison. Un dossier "
        "qui contient autre chose que Gerbil est refusé, car la mise à jour supprime les anciens fichiers du "
        "programme.",
    "packaging/gerbil_setup.pyw:install": "Installe : supprime les fichiers de la version précédente (pas les modèles "
        "d'IA), extrait l'archive avec une progression, écrit Uninstall.bat et la liste des fichiers, crée les "
        "raccourcis et l'entrée de désinstallation de Windows.",
    "packaging/gerbil_setup.pyw:register": "L'entrée dans « Applications installées » de Windows (pour l'utilisateur "
        "seul).",
    "packaging/gerbil_setup.pyw:Setup": "La fenêtre de l'installateur.",
    "packaging/gerbil_setup.pyw:Setup.__init__": "La fenêtre : dossier, raccourci sur le bureau, bouton Install, "
        "progression.",
    "packaging/gerbil_setup.pyw:Setup.browse": "Choisit le dossier ; un dossier parent reçoit un dossier « Gerbil ».",
    "packaging/gerbil_setup.pyw:Setup.start": "Vérifie le dossier et que Gerbil est fermé, puis installe dans un fil "
        "d'exécution séparé (la fenêtre reste réactive).",
    "packaging/gerbil_setup.pyw:Setup.finished": "Fin de l'installation : erreur affichée, ou « Open Gerbil » proposé.",
    "packaging/gerbil_setup.pyw:Setup.launch": "Lance le Gerbil installé (dans un environnement propre) et ferme.",
    "packaging/gerbil_setup.pyw:main": "Ouvre la fenêtre de l'installateur (nette sur les écrans haute résolution).",

    # ======================================================================== tests
    "tests/synthetic.py:__module__": "Des photos synthétiques pour les tests : un tesson et une échelle à damier "
        "imprimée (cases de 1 cm, deux rangées), sur fond clair ou sur feutre sombre (avec une étiquette papier). "
        "Rien de réel : le dépôt ne contient aucune photo.",
    "tests/synthetic.py:sherd_polygon": "Le contour irrégulier d'un tesson inventé (un polygone).",
    "tests/synthetic.py:scale_image": "Une échelle à damier : deux rangées de cases de 1 cm × 0,5 cm, noires et "
        "blanches, sur un carton blanc.",
    "tests/synthetic.py:photo": "(image RVB, masque du tesson, px/cm) : le tesson en haut au milieu, l'échelle "
        "dessous ; avec shadow, le tesson projette une ombre douce vers le bas et la droite.",
    "tests/test_gerbil.py:__module__": "Les vérifications automatiques de Gerbil sur des photos synthétiques : "
        "échelle, détourage, étiquettes sur fond sombre, échelles apprises, métadonnées IPTC, planches, "
        "inventaire. Lancer : py -3 -m pytest tests.",
    "tests/test_gerbil.py:save": "Enregistre une photo synthétique.",
    "tests/test_gerbil.py:run": "Lance le moteur sur un dossier de test (sans PSD) et renvoie les lignes du rapport.",
    "tests/test_gerbil.py:number": "Lit un nombre du rapport (virgule décimale).",
    "tests/test_gerbil.py:light": "Le lot partagé de photos synthétiques sur fond clair, traité une fois.",
    "tests/test_gerbil.py:test_scale_read_exactly": "L'échelle à damier est trouvée et lue à 0,5 % près (100 px/cm), "
        "longueur 10 cm.",
    "tests/test_gerbil.py:test_cutout_matches_the_sherd": "Le détourage a la surface du vrai tesson à 3 % près, et le "
        "TIFF est à 254 ppp (100 px/cm) : la vraie taille.",
    "tests/test_gerbil.py:test_dark_background_label_discarded": "Sur feutre sombre, l'étiquette papier est écartée, un "
        "seul morceau est gardé, sans liseré sombre (surface à 4 % près).",
    "tests/test_gerbil.py:test_no_scale_still_discards_the_scale": "Sans échelle (--no-scale), l'échelle de la "
        "photo est quand même écartée : un seul morceau, le tesson, à 3 % près de sa vraie surface.",
    "tests/test_gerbil.py:test_cast_shadow_removed": "Une ombre portée douce est retirée : le détourage a la "
        "surface du tesson seul, à 3 % près.",
    "tests/test_gerbil.py:test_learned_scale": "Une échelle apprise est retrouvée sur une autre photo, à 0,5 % près.",
    "tests/test_gerbil.py:test_iptc_and_lossless_jpeg": "Les champs IPTC sont remplis d'après le modèle, et le XMP "
        "inscrit dans un JPEG laisse son image identique pixel pour pixel.",
    "tests/test_gerbil.py:test_plates_svg": "La planche SVG est en A4 (210 × 297 mm) et l'objet y a sa vraie taille au "
        "1:2.",
    "tests/test_gerbil.py:test_inventory_and_powershell": "L'inventaire CSV lit les champs des noms, et la ligne "
        "PowerShell est construite (Get-ChildItem, $Matches, Export-Csv).",
}
