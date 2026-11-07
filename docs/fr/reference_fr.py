"""Explications en français des fonctions et classes de Gerbil (guide du code en français).
Clé : "fichier:Classe.fonction" (comme les docstrings en anglais du code). Une fonction absente ici
apparaît dans le guide avec son explication anglaise, signalée comme « à traduire »."""

FR = {
    # ======================================================================== gerbil.py
    "gerbil.py:__module__": "Le moteur de Gerbil : détourage des objets photographiés avec une échelle, à leur taille "
        "réelle (1:1). Pour chaque photo NOM.JPG, dans un dossier « outlined_result » à côté des photos : la copie "
        "de la photo, NOM.psd (calques « Original photo » masqué, « Scale », « Ceramic », avec masques de fusion "
        "modifiables), NOM_outlined.tif (l'objet seul), NOM_outlined_scale.tif (l'objet et l'échelle), l'aperçu de "
        "contrôle (to_control) et une ligne du rapport outlined_report.csv. En cas de doute, les fichiers "
        "reçoivent le suffixe « _to_be_verified ». L'échelle donne la résolution réelle de chaque photo, inscrite "
        "dans les fichiers : déposés dans Illustrator, ils s'affichent à 1:1.",
    "gerbil.py:Photo": "Une photo telle que le moteur l'utilise : chemin, pixels RVB (redressés), profil couleur ICC, "
        "EXIF, et les informations de prise de vue (appareil, objectif, date) gardées pour le rapport et les "
        "métadonnées.",
    "gerbil.py:_txt": "Une valeur EXIF en texte propre : octets décodés (Latin-1), zéros et espaces de fin retirés.",
    "gerbil.py:_rational": "Un nombre EXIF écrit en fraction XMP (« 1/125 »), comme le demande le format XMP.",
    "gerbil.py:_xmp_date": "Une date EXIF « 2025:12:01 21:03:55 » réécrite au format XMP « 2025-12-01T21:03:55 ».",
    "gerbil.py:develop_raw": "Développe une photo RAW avec LibRaw (bibliothèque rawpy) : balance des blancs de "
        "l'appareil, sRVB, 8 bits, redressée. L'interface la développe de la même façon, pour que les coordonnées "
        "correspondent.",
    "gerbil.py:load_photo": "Ouvre une photo comme le moteur en a besoin : pixels RVB 8 bits redressés selon "
        "l'orientation EXIF (les RAW passent par develop_raw), EXIF, profil couleur ICC, et les informations de "
        "prise de vue pour le rapport et le XMP. Renvoie une Photo.",
    "gerbil.py:srgb_profile": "Le profil couleur sRVB standard (ICC), inscrit quand la photo n'en a pas.",
    "gerbil.py:output_exif": "Copie des métadonnées de prise de vue, mise à jour pour le fichier détouré (orientation, "
        "résolution, logiciel).",
    "gerbil.py:to_lab": "Convertit l'image RVB en CIELAB (L* clarté de 0 à 100, a* et b* couleur autour de 0) : en Lab, "
        "les différences de couleur correspondent à ce que voit l'œil, ce qui rend mesurable « différent du fond ».",
    "gerbil.py:distance": "Distance de couleur de chaque pixel au modèle du fond (en Lab) ; la clarté est pondérée par "
        "l_weight, car une ombre change plus la clarté que la couleur.",
    "gerbil.py:poly_terms": "Les termes x^i × y^j d'un polynôme à deux variables de degré deg : le modèle du fond est un "
        "tel polynôme ajusté sur le fond, pour suivre un dégradé d'éclairage.",
    "gerbil.py:BackgroundModel": "La couleur du fond (en Lab), modélisée par un polynôme en x et y (dégradé de lumière).",
    "gerbil.py:BackgroundModel.__init__": "Ajuste la couleur du fond de la photo : une surface polynomiale par canal Lab, "
        "ajustée par moindres carrés sur les pixels qui ressemblent au fond (en plusieurs passes, l'objet et "
        "l'échelle étant écartés) ; décide aussi si le fond est sombre (velours, feutre).",
    "gerbil.py:BackgroundModel.evaluate": "La couleur du fond sur une zone de l'image (rectangle donné en pixels).",
    "gerbil.py:hysteresis": "Seuillage par hystérésis : garde les régions au-dessus du seuil bas qui contiennent au moins "
        "un pixel au-dessus du seuil haut (un bord pâle est gardé s'il appartient à un objet net).",
    "gerbil.py:fill_holes": "Bouche les trous du masque (reflets de glaçure, concrétions claires), sauf les vraies "
        "ouvertures : trous assez grands dont la couleur moyenne est celle du fond (anse, perforation).",
    "gerbil.py:cast_shadows": "Fond clair : les ombres portées gardées par la règle de couleur. Une ombre est plus "
        "sombre que le fond mais de sa couleur, lisse, le long du contour, et se fond dans le fond (bord "
        "extérieur flou, alors que le bord d'un objet est net). Renvoie leur masque, ou None.",
    "gerbil.py:disk": "Élément structurant en forme de disque de rayon r, pour la morphologie (érosion, dilatation…).",
    "gerbil.py:scale_ink_classes": "Les pixels noirs et rouge vif : les cases colorées d'une échelle archéologique.",
    "gerbil.py:straighten": "Extrait une vignette de taille donnée centrée sur un point, tournée pour que la direction "
        "theta devienne horizontale (l'échelle est ainsi « redressée » pour être lue).",
    "gerbil.py:apply_affine": "Applique une matrice affine 2 × 3 à des points : rotation, mise à l'échelle et translation.",
    "gerbil.py:_runs": "Les suites de valeurs égales d'un profil (lecture des cases) : [[valeur, début, fin], …].",
    "gerbil.py:_merge_runs": "Réunit les suites consécutives de même valeur.",
    "gerbil.py:_clean_runs": "Supprime les suites intérieures les plus courtes (bruit, chiffres) jusqu'à ce qu'elles "
        "aient toutes une longueur minimale.",
    "gerbil.py:_crossing": "Position au sous-pixel où le profil traverse 0,5 près de x (bord d'une case).",
    "gerbil.py:analyze_pattern": "Première lecture d'un damier, sur la vignette où l'échelle est horizontale : position "
        "de la face imprimée, nombre de cases et leur longueur. Les pixels venus de hors de la photo ne sont pas "
        "lus ; une case coupée par le bord est comptée mais exclue de la mesure.",
    "gerbil.py:_inside": "Les pixels d'une vignette redressée qui viennent de l'intérieur de la photo.",
    "gerbil.py:_fit_comb": "Ajuste une suite régulière x_k = a0 + pas × k sur des positions (phase commune, puis moindres "
        "carrés en rejetant les écarts trop grands) : c'est le « peigne » des limites de cases ou des graduations.",
    "gerbil.py:analyze_comb": "Seconde lecture d'un damier, utilisée quand la première échoue : elle tolère les chiffres "
        "imprimés dans les cases (« 5 », « 10 », « cm ») et n'importe quel nombre de cases. Les limites des cases "
        "sont là où le profil signé (encre de la rangée du haut moins celle du bas) change de signe ; un chiffre "
        "affaiblit le profil dans sa case sans changer son signe. Les limites sont ajustées par un peigne régulier, "
        "ce qui mesure la case sur toute la longueur de l'échelle.",
    "gerbil.py:Scale": "Une échelle trouvée (ou donnée) : px/cm, nombre de cases, longueur, angle, contour dans la photo, "
        "zone élargie (support, pâte à fixe), vignette redressée et sa matrice, détails de lecture, note, doutes et "
        "nature (damier, réglet, manuelle, apprise).",
    "gerbil.py:_rect_axis": "Angle du grand côté d'un rectangle tourné, et ses grand et petit côtés.",
    "gerbil.py:_single_row_groups": "Échelle à une seule rangée : ses cases noires ne se touchent pas ; cherche des taches "
        "pleines de même taille, alignées et régulièrement espacées.",
    "gerbil.py:_card_side": "Échelle à une rangée terminée par une case blanche : de quel côté continue le carton.",
    "gerbil.py:_scale_on_dark": "Fond sombre (velours noir) : les cases noires se confondent avec le fond. L'échelle est "
        "cherchée à partir de ses cases claires : pour chaque groupe de taches claires allongé, tout ce qui est "
        "autour est peint en blanc, pour que l'échelle ressemble à ce qu'elle serait sur fond clair, puis la "
        "détection habituelle est lancée.",
    "gerbil.py:_glyph_vector": "Un signe imprimé, recadré, mis à une taille fixe et normalisé, pour être comparé à des "
        "modèles de chiffres.",
    "gerbil.py:_glyph_templates_get": "Les modèles de chiffres et de « c », « m », dessinés avec les polices de Windows.",
    "gerbil.py:digits_upside_down": "L'échelle est-elle à l'envers ? Les signes imprimés dans les cases (« 5 », « 10 », "
        "« cm ») sont comparés aux modèles de chiffres, à l'endroit et retournés : le sens le plus ressemblant "
        "l'emporte. Sur 1 265 échelles d'orientation connue, aucune erreur.",
    "gerbil.py:manual_scale_entry": "L'échelle donnée à la main pour cette photo (fenêtre « Set scale… »), lue dans "
        "gerbil_scales.json à côté des photos : deux points, la longueur entre eux, la largeur de l'échelle.",
    "gerbil.py:manual_scale": "Échelle à partir de deux points de distance connue : px/cm = distance / longueur. Le "
        "calque de l'échelle est une bande de la largeur donnée autour du segment, redressée.",
    "gerbil.py:find_profile": "Le profil de site d'une photo : le fichier donné (--profile), sinon gerbil_profile.json "
        "dans le dossier de la photo.",
    "gerbil.py:load_profile": "Lit un profil de site (fond, échelles apprises, ordre de recherche) et prépare ses "
        "échelles pour la comparaison (mis en cache).",
    "gerbil.py:learn_scale": "Apprend une échelle à partir de deux points d'une photo : la bande de l'échelle entre les "
        "deux points, redressée, gardée en image de 2 400 px de long avec son px/cm.",
    "gerbil.py:detect_learned_scale": "Cherche les échelles apprises sur la photo. D'abord grossièrement : des points "
        "caractéristiques (SIFT) appariés entre le modèle et la photo, une position, une taille et un angle "
        "communs trouvés par RANSAC ; puis finement : le modèle est corrélé à la photo (ECC), ce qui mesure la "
        "longueur à mieux que 0,1 % quand c'est la même échelle physique.",
    "gerbil.py:detect_scale": "La détection de l'échelle : damiers (première et seconde lecture), échelle à une rangée, "
        "réglet, fond sombre ; vérifications (longueur habituelle, régularité), mesure fine à pleine résolution, "
        "orientation par les chiffres.",
    "gerbil.py:_thin_ticks": "Les traits sombres fins et allongés : les graduations d'un réglet.",
    "gerbil.py:_tick_combs": "Regroupe les traits parallèles, côte à côte et régulièrement espacés : une rangée de "
        "graduations.",
    "gerbil.py:_peaks": "Les maxima locaux d'un profil, espacés d'au moins 0,55 pas, au sous-pixel.",
    "gerbil.py:analyze_ruler": "Lit un réglet redressé : pas du millimètre et graduations du centimètre (seconde passe "
        "robuste pour les graduations épaisses).",
    "gerbil.py:ruler_outline": "Les bords du carton du réglet.",
    "gerbil.py:detect_ruler": "Réglet gradué en millimètres : mesure le pas du millimètre sur toute la longueur ; "
        "seconde passe pour les graduations épaisses et longues.",
    "gerbil.py:poly_mask": "Le masque d'un polygone (coordonnées au sous-pixel).",
    "gerbil.py:discard_labels": "Écarte ce qui n'est pas l'objet : ce qui est de l'autre côté de l'échelle (étiquettes "
        "sous le réglet), les éléments partout plus fins que 1,7 mm (écriture au feutre, lignes d'un sachet), et "
        "les petits éléments isolés loin de l'objet (sauf sur fond sombre, où ce sont de petits tessons).",
    "gerbil.py:translucent_supports": "Les supports en plexiglas : régions de la couleur du fond, qui dépassent de "
        "l'objet ; un reflet du fond sur une glaçure noire est distingué (plus sombre, le long de la céramique).",
    "gerbil.py:colour_chart": "Reconnaît une charte couleur (colorimètre Pantone, ColorChecker…) : beaucoup de teintes "
        "saturées différentes, alors qu'une céramique, même peinte, reste dans quelques teintes voisines.",
    "gerbil.py:chart_disc": "Le cercle d'une charte ronde, ajusté sur ses encres de couleur.",
    "gerbil.py:remove_charts": "Retire les chartes couleur du masque, avec leur ombre portée quand une charte touche "
        "la céramique.",
    "gerbil.py:label_card": "Une étiquette papier sur fond sombre : claire, blanche, bleutée (azurants) ou jaune pâle, "
        "et rectangulaire ; ou très rectangulaire et claire, quelle que soit sa couleur (un tesson cassé ne remplit "
        "jamais autant son rectangle).",
    "gerbil.py:straight_outline": "La part du contour d'un morceau (hors bords de la photo) faite de longs côtés "
        "droits, parallèles ou perpendiculaires à sa direction principale : près de 1 pour une barre d'échelle "
        "(même en L), un réglet, une étiquette ou une charte, plus bas pour un tesson cassé, une monnaie ou un "
        "outil. Le contour est d'abord fermé, pour que les graduations d'un réglet ou les cases d'une échelle "
        "fassent un côté droit. Renvoie aussi le remplissage de son rectangle.",
    "gerbil.py:printed_element": "Une barre d'échelle, un réglet, une étiquette ou une charte, reconnus sans les "
        "mesurer (pas d'échelle trouvée) : contour droit et contenu d'un imprimé (noir et blanc, peu coloré, ou "
        "rectangle plein ; voir les constantes PRINT_*).",
    "gerbil.py:split_labels": "Fond sombre : une étiquette qui touche un objet par un coin forme une seule tache avec "
        "lui ; la tache est coupée à ses jonctions étroites et la partie « étiquette » est retirée.",
    "gerbil.py:edge_at_half_contrast": "Fond sombre : le bord d'un objet clair est un dégradé de plusieurs pixels ; le "
        "bord du détourage est placé au milieu de ce dégradé (pas de liseré sombre), sans toucher l'intérieur.",
    "gerbil.py:outline_ceramic": "Le détourage : premier masque sur la photo réduite (distance de couleur au fond, "
        "hystérésis, trous bouchés), tri des morceaux (zone de l'échelle, étiquettes, supports, chartes, éléments "
        "isolés), affinage à pleine résolution, bord adouci. Renvoie le masque et ce qui a été écarté.",
    "gerbil.py:find_putty": "Cherche la pâte à fixe accrochée à la céramique : une partie du contour séparée par deux "
        "concavités, nettement plus lisse, plus claire et moins colorée que la céramique. Seul le masque change.",
    "gerbil.py:ai_model_path": "Le fichier d'un modèle d'IA, dans le dossier « models » ; téléchargé la première fois "
        "et vérifié par sa somme MD5.",
    "gerbil.py:ai_providers": "Carte graphique si onnxruntime en propose une (CUDA, ou DirectML sous Windows), sinon le "
        "processeur.",
    "gerbil.py:_ai_open": "Ouvre un modèle ONNX avec onnxruntime, en partageant le processeur entre les photos "
        "traitées en parallèle.",
    "gerbil.py:ai_mask": "Le second avis de l'IA : probabilité « objet » de chaque pixel, calculée par le réseau (IS-Net "
        "ou BiRefNet) sur la photo réduite à 1 024 × 1 024.",
    "gerbil.py:click_model_path": "Le fichier du modèle « un clic », téléchargé la première fois (vérifié par SHA-256).",
    "gerbil.py:ClickCutout": "Le détourage de l'objet sur lequel l'archéologue clique : Segment Anything sait quel "
        "objet détourer et n'a plus à deviner ce qui est un tesson, une étiquette, une ombre ou le fond. Son bord "
        "étant grossier, le bord du détourage calculé est gardé là où il est d'accord.",
    "gerbil.py:ClickCutout.__init__": "Charge les deux parties de MobileSAM (encodeur d'image, décodeur de masque).",
    "gerbil.py:ClickCutout.set_image": "Encode la photo une fois (environ une seconde) : les clics sont ensuite immédiats.",
    "gerbil.py:ClickCutout.mask": "Le masque de l'objet désigné par des points cliqués.",
    "gerbil.py:click_refine": "Le bord de l'objet cliqué : celui du détourage calculé là où il est d'accord avec "
        "Segment Anything, celui de Segment Anything ailleurs.",
    "gerbil.py:Layer": "Un calque des fichiers produits : nom, position, pixels, masque, visible ou masqué.",
    "gerbil.py:extract": "Une découpe d'image, complétée de blanc là où elle dépasse.",
    "gerbil.py:composite": "Fusionne les calques visibles sur un fond transparent.",
    "gerbil.py:decontaminate_edge": "Fond sombre : les pixels du bord mêlent la couleur de l'objet et celle du fond (fin "
        "liseré sombre). Leur couleur est remplacée par celle de l'objet juste à l'intérieur, sans changer le "
        "contour.",
    "gerbil.py:layout": "Construit les calques des fichiers : l'objet et son masque, l'échelle (redressée sous l'objet, "
        "ou là où elle a été photographiée), la photo entière (calque masqué), les marges.",
    "gerbil.py:_packbits_block": "Compression PackBits (le RLE de Photoshop) d'un bloc de lignes, avec numpy.",
    "gerbil.py:packbits": "Compression PackBits d'un canal entier.",
    "gerbil.py:rle_channel": "Un canal tel que Photoshop l'enregistre (compression RLE).",
    "gerbil.py:_pascal": "Une chaîne Pascal (longueur puis texte), comme dans le format PSD.",
    "gerbil.py:_resource": "Un bloc de ressource d'image PSD (« 8BIM »).",
    "gerbil.py:_unicode": "Une chaîne Unicode du format PSD.",
    "gerbil.py:_xml": "Protège &, < et > pour le XML.",
    "gerbil.py:iptc_values": "Les champs IPTC d'une photo : le modèle du projet (sinon le modèle par défaut) rempli avec "
        "ses valeurs.",
    "gerbil.py:_iptc_prop": "Une propriété XMP en RDF : texte, texte dans une langue, ou liste.",
    "gerbil.py:make_xmp": "Le paquet de métadonnées XMP : description de l'échelle, informations de prise de vue, champs "
        "du renommage en lot et champs IPTC du projet.",
    "gerbil.py:embed_xmp_jpeg": "Inscrit le XMP dans un JPEG sans toucher à l'image : le segment XMP est remplacé ou "
        "ajouté, l'image compressée est recopiée octet pour octet.",
    "gerbil.py:write_sidecar": "Écrit NOM.xmp à côté d'une photo (lu par Bridge, Lightroom, darktable) ; un .xmp écrit "
        "par un autre logiciel n'est jamais remplacé.",
    "gerbil.py:write_psd": "Écrit le fichier Photoshop à calques, octet par octet : en-tête, résolution en cm, profil "
        "ICC, EXIF et XMP, calques avec leurs masques, image fusionnée.",
    "gerbil.py:write_tiff": "Écrit un TIFF (transparent ou sur blanc, LZW / ZIP / sans compression) à la résolution 1:1, "
        "avec profil ICC et métadonnées.",
    "gerbil.py:font": "Une police TrueType pour les textes de l'aperçu de contrôle.",
    "gerbil.py:control_image": "L'aperçu de contrôle : photo réduite, contour du détourage en vert, échelle en magenta, "
        "ce qui a été écarté en rouge, retiré par l'IA en cyan, informations principales écrites dessus.",
    "gerbil.py:output_paths": "Les chemins des fichiers d'une photo, avec _to_be_verified en cas de doute.",
    "gerbil.py:remove_stale": "Après un nouveau traitement, supprime l'ancienne variante (avec ou sans "
        "« _to_be_verified ») des fichiers réécrits.",
    "gerbil.py:copy_original": "Copie la photo originale dans le dossier de résultats.",
    "gerbil.py:load_project": "Le projet de renommage d'un dossier (gerbil_project.json) : champs, modèle de nom, règle, "
        "valeurs communes et valeurs de chaque photo.",
    "gerbil.py:photo_values": "Les valeurs d'une photo : celles communes au projet, complétées par les siennes.",
    "gerbil.py:project_name": "Le nom de sortie construit à partir du modèle ; caractères interdits remplacés par « _ », "
        "séparateurs laissés par des champs vides réunis.",
    "gerbil.py:rule_regex": "La règle de nommage telle que l'opérateur -match de PowerShell la lit (expression "
        "régulière .NET, sans distinction de casse).",
    "gerbil.py:project_checks": "Les raisons de douter des informations d'une photo : champ obligatoire vide, nom hors "
        "de la règle.",
    "gerbil.py:plan_names": "Décide, avant le traitement, du nom de sortie et des informations de chaque photo ; deux "
        "photos ne peuvent pas avoir le même nom (suffixe _2, _3…).",
    "gerbil.py:edits_entry": "Les corrections faites à la main pour cette photo (masque corrigé, angle).",
    "gerbil.py:cutout_from_mask": "Le détourage à partir d'un masque corrigé à la main, avec le même bord adouci.",
    "gerbil.py:write_review": "Écrit le masque et le contour de l'échelle d'une photo pour la fenêtre de vérification.",
    "gerbil.py:rotated_ceramic": "L'objet tourné de l'angle décidé dans la fenêtre de vérification (une seule "
        "rééchantillonnage).",
    "gerbil.py:process_photo": "Traite une photo de bout en bout : lecture, modèle du fond, échelle, détourage, pâte à "
        "fixe, fichiers PSD et TIFF, aperçu, métadonnées, ligne du rapport.",
    "gerbil.py:_init_worker": "Chaque processus de travail limite OpenCV à 2 fils (les photos sont déjà traitées en "
        "parallèle).",
    "gerbil.py:list_photos": "Les photos des dossiers donnés ; les fichiers produits par Gerbil qui seraient parmi les "
        "photos sont ignorés.",
    "gerbil.py:_HelpFormatter": "Affiche la valeur par défaut d'une option seulement quand elle a un sens.",
    "gerbil.py:_HelpFormatter._get_help_string": "L'aide d'une option.",
    "gerbil.py:main": "La ligne de commande : lit les options, liste les photos, prévoit leurs noms, les traite en "
        "parallèle, écrit le rapport et affiche le bilan des problèmes.",
    "gerbil.py:previous_output": "Le nom de sortie qu'avait la photo au traitement précédent.",
    "gerbil.py:remove_renamed": "Supprime les fichiers d'une photo écrits sous un ancien nom (le nom du projet a changé).",
    "gerbil.py:write_report": "Écrit le rapport CSV (Excel : séparateur « ; », virgule décimale), en gardant les lignes "
        "des autres photos.",
    "gerbil.py:print_summary": "Le bilan de fin : ce qui est à vérifier, regroupé par problème.",
    "gerbil.py:print_row": "Une ligne d'avancement pour une photo : [i/n] nom : état (échelle, durée) | doutes et notes.",
    "gerbil.py:_own_console": "Vrai quand le programme a sa propre console visible (exe double-cliqué).",
}
