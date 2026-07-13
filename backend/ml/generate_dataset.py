"""
generate_dataset.py

Builds the labeled training corpus for document classification.
Combines:
  - Real OCR output already captured from the pipeline (declaration, constat)
  - Synthetic templated examples for all 7 classes, with light noise injection
    to mimic realistic OCR errors (since the classifier must be robust to the
    same noise patterns the real OCR pipeline produces).

Output: ml/data/documents_dataset.csv  (columns: text, label)
"""

import csv
import random
import unicodedata
import re
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from text_utils import clean_text

random.seed(42)

LABELS = [
    "declaration_sinistre",
    "carte_grise",
    "permis_conduire",
    "facture",
    "devis",
    "constat_amiable",
    "rapport_expertise",
]

# -----------------------------------------------------------------------
# 1. REAL SAMPLES — actual OCR output already captured from your pipeline
#    (raw text, uncleaned — cleaning happens later in the pipeline, same
#    as it will for live documents)
# -----------------------------------------------------------------------

REAL_SAMPLES = [
    ("carte_grise", """155e n republique tunisienne e r a certificat d immatriculation lss/i jesnaus sokg d f i . - nou et pronem j l es . ls e 3 g3 a 05355012 cn fou aui 29 420 r . e u n serie du type . acivee lisx y 3kpa341able283793 dals se ce e d lala constructeur hos4k461f typoconstructeur s003 10 s l-3 91 type commercal 2020/07/07 0c ydu hn u zn f ij 4h l / 0 2207 - t u 1 e"""),
    ("carte_grise", """ck as ss aaygeazl y republique tunisienne jl 5159 ministere du transport certificat d immatriculation immatriculation 123 uy 4567 date de lo premiero mise en crcufation 15/06/2018 marque peugeot type 308 enorge 477 2 essence puissance fiscale - 7 cv nornbre de places . 5 usage - . particulier numero d idenulication 6u vehicute. vf3lcshpjs123456 proprietaire c - adresse 200 45 rue de la liberte r 1002 tunis l- le ministe du transport a 1234567 //o """),
    ("constat_amiable", """constat amiable d accident automobile dute ge l acode-e 12 / 0s / 2024 love ueu tunis ticurose 14 30 tuunis - avenue habib bours bq mt p vemicutez 12 cinconstances t denicuce proes d eamserce / auare 3s 3 prores coaurarce l eract akmed ben safah commorc a noiee kacim gharbi n contat 00123456 foemura gas temtnte o r cotat 7834s612 o fcnemec ce 6e cecote u sootse d evnsance - ami assurances fextrerdos ocionce soutte jarurarce star assurances vencue tona 0 6ra mt a mucue feugeot. dornveut. vises renauct. type - 308 te -ctio n d ermaineuldon 123 uiys 4sgt n d mmatnculation 456 us t8io croquis de l accidont 12 cirecsao c orseras 1b degsts appurenes pare-chocs avant phare 3auck degats opparems porte arriere droite aile droite signature des conductours jh hhe u """),
    ("constat_amiable","""constat amiable d accident automobile ne cc nstn uc pas une reconnaissance de rcsponsabnhte. mais un releve a signer obligatoirement par les deux conducteurs des identites et des faits. servant a l acceleratton du reglement 1. date de l accident i heure 3. blesses meme legers 4. degats materiels autres s. temoins noms adresses et tel a soungner s il s agit dun passager de a ou b1 qu aux vehicules a et b k vehicule a 12. circonyances mehicule b i r mettre une croix x dans l m eqs - 6. societe d assurances chacune des cases utiles / 6. societe d assurances pour preciser le croquis vehicule assure par vehicule assure par .. en stationnement 1 1 a police d assurance n police d assurance n 2 quittalt un stationnement 2 i agence h agence attestation valable 3 prenalt un statlonnement 3 attestation valable . du au 7. identite du conducteur e 4 sortait d un parking d un lleu 4 prive d un chemin de terre du au 7. identite du conducteur 5 s engagealt dans un parking un 5 neu prive un chemin de terre nom nom p e e preno 6 arret de circulation 6 prenom ms adresse permis de conduire n 0 4 delivre le adresse 7 trotiement sans changement de file 7 permis de conduire n 8 heurtait a l arriere en roulant dans 8 le meme sens et sur une meme file y roulait dans le meme sens et s sur une fiie differente delivre le 8. assure voir attest. d assur. 8. assure voir attest. d assur. g 033f p e s t 10 changealt de file 10f nom 9 nom prenom 11 doublalt 11 prenom p adresse 12 virait a droite 12kl a adresse tel. 9. identite du vehicule marque type tfel. 13 virait a gauche 13 9. identite du vehicule marque type 14 reculait 14h- 15 empletait sur la partie de chaussee 15 reservee a la circulation en sens n d immatriculation n d immatriculation inverse sens suivi 16 venalt de droite dans un 16 sens suivi carrefour venant de 17 n avalt pas observe le signal 17 . a venant de de priorite allant a allant a iindiquer le nombre dee e ps - cases marquees d une croix 10. indiquer par une fleche estes dstque rs cune ctoux . rr 10 indiquer par une ecne le point de choc initial 13 croquis de i acmdent g ren le point de choc initial 77 l y n xt . . .it . 1 l i t 10 ..l- l l-4 - l- - ---.l i r- . l . l..- k - y z ga -w p wr litt kn su e e s p d 660 - .l- hjh 440 g i i 44 i r - t .-- ..-l l . .aa. -4 -e3- . a .l .4 - -.. - 14. observations 14. observahons u a 15 signature des conducteurs b cileil gase p-a5jl ol l h3l 4.jlule xiuaslf glel 53114 ug.ll enolall sll su lg sl ce 85 guao da us pallle ela mel 1 1 nb exigez une photocopie de l attestation internationale d assurances carte verte ou carte orange si le tiers est assure a l etranger. 11. degats apparents ll1. degats apparents . 4 de lgl tl a remplir par l assure et a transmettre dans les cinq jours a son assureur dans les 24 heures en cas de vol du vehicule . 1. nom de l assure 4s 1n profession le souscripteur n tel. 2. cil consigdcgs de qccident croquis seulement s il n a pas deja ete fait sur le constat au recto . designer les vehicules par a et b conformement au recto preciser 1. le trao6 des voles - 2 la direction des vehicules a b - 3. leur position au moment du choc - 4. les signaux routlers - 5 le nom des rues ou routes 3. a-t-il ete etabli un proces-verbale de la garde nationale un rapporl de polico si oui brigade ou poste de police a conducteur du vehicule assure est-il le conducteur habituel du vehicule .. ...... our non date de naissance ... o oi i oei i oo est-il salarie de l assure lou sinon a quel titre conduisait-il 5. vehicule assure lieu habituel de garage quel etait le inotif du deplacement expertise des degats garage ou le vehicule sera visible quand eventuellement telephoner a a ete vole indiquer son numero dans la serie du type voir carte grise l est gage nom et adresse de l organisme de credit l si le est un poids lourd poids total en charge vehicule etait attale a un autre vehicule tractant ou remorque au moment de l accident indiquer ie n d immaniculation de cet autre vehicuie . ppids total en charge nom de la societe qui l assue 1n police dans cette societe b. degals materiels autres qu aux vehicules a et b nature et importance nom et adresse du proprietaire 7. blesse s nom...... prenom et age adresse es .. profession.. . . . . . .. .ns0eere degre de parente avec l assure ou le conducteur.. ........ ... ... est-il salarie de l assure .. ... .... nature et gravite aes biessures.... situatlon au moment de l accident pleton passager du vehicule a ou b etc. 1 soins ou hospitalisation a..... 7 jar e p slgnature de l assure e """),
    ("declaration_sinistre", """g2 en declaration de sinistre assurances l1jinformations sur l assureeb nometprenom ahmed ben salah adresso 5 rue de la liberte .1002 tunis t6 . 98 123 456 emoi ahmed.bensalah email.tn n convat 00f25 56 ls datedusnsue 12 / os / 2024 houre 14 30 leu avenue habib bour3uiba tunis noture dusinistre accident de la circulation circonstances getolliees choc avec un autre vehicule a un carrefour. degafs materiels importants. nometprenom karim gharbi tel 95 654 321 aasurance . star assui gaccs n convot 78945612 fota tunis le 12 / 05 / 2024 9 o we f / """),
    ("declaration_sinistre","""7 declaration de sinistre d assurance nord-est m compagnie date de la dectaration 14/03/2025 numero de police 4471-8829-03 l informations du client nom martin prenom sophie adresse 27 rue des lilas 25011 paris telephone q6 42 18 93 27 email soehie.mar n em l. y 1. details du sinistre 12/03/2025 a 14h30 lieu garage souterrain 27 rue des lilas type de sinistre vol d objet gersonnel description sac a main en cuir noir contenant orteleuille endant stotionnement. date du sinistre telephone gorfa.ble iphone 14 et cles vole p i. dommages estimes montant estime 4 850 iv. pieces jointes a proces-verbal de depot de plainte n 2025-031 4-0892 h factures d achat des objets voles k photos du lieu du sinistre v. signature so hie maroh fait a paris le 14 mars 2025 """),
    ("declaration_sinistre","""4 // //////// 72 - / c- es . e si c /i -ahy / f 4 g / 7 c00 peclaration de sinistre compaun e 0 a5 urance horo-est poice 4at1-8828-03 numero de jectaration 14 mars 2025 surle client // nom artin a prenem sophie 4 adresse 23 r des lilas 3501 paris /a telepmne q 42 18 93 33 / teiephone 06 nha l0 adefails du sinistre date aheure w i c l 3e souterrain 29 cue dm p e ekg4r oni lieu type de sinistre yol d g4yi portable macpook pro ma a ede dole itee tat pohe j4hoo0 date de la d description un ordinateur la c i -giace - uf a i en tait verrov une trace d e mc fon est visible spf le loz 7 i mais i //// montant estime des dommages l 8 30 // / t preces jointes 7 / e p o es-varbal de depot de pleinte e 2025 03hz-4471 e a facture g achat originale cr 50 photos des dogits 3 clches cn a ps m senature 01 declara / lo 44 mars 2025 fan a parie / 21 """),
    ("declaration_sinistre","""declaration de sinistre compagnie d assurance nord-est n police . ne-2024-088317 12 rue des tilleuls - 75011 paris tel ot 445566 77 1. renseignements sur le sinistre date du sinistre 14/03/2024 heure approximative 19h45 lieu du sinistre 23 avenue du parc 35016 paris type de sinistre incendie degats des eaux consecutifs l t f i1. description des dommages incendie declare dans la cuisine vers 19h45 propagetion limitee au placard dane remarent et et an des trainr att plavie ine prari didi deut flatieig ex stratifie. intervention des pompiers a 20m2.k eaaju utisr pourl extinotirn andommage le nparquet cart evike f d ne rr djcent cloison latre aucun blesse. il estimation preliminaire des dommages placard cuisine 450 plan de travail 320 parquet 3 m 280 cloison platre 180 total 1 230 iv. temoins / intervenants pompiers paris 16 intervention n 2024-0314-088 m. laurent dubois voisin n 25 temom oculaire / / a v. pieces jointes photographies des deaats g clich s declaration des pompiers devis fait a paris le 15 mars 2024 signature du declarant sophie marchand """),
    ("declaration_sinistre","""hmi declaration de sinistre n 0352419 assurances i q lis u a adresser dans les 5 jours 1 informations sur l assure nom et prenom ahmed ben salah assureur ami assurances adresse 45 rue de la liberte agence tunis centre 1002 tunis tel. 98 1423 456 date d effet du contrat 45/03/2023 email ahmed.bensalah email.tn 00123456 n contrat 2. informations sur le sinistre date du sinistre 42 7 05 7 2024 heure 44 30 ya-t-ildesblesses doui f non si oui nombre lieu du sinistre avenue habib bourquiba y a-t-il un constatamiable x oui non si oui le joindre a la presente declaration. nature du sinistre accidenf de la circulation les autorites ont-elles ete avisees oou k non circonstances detaillees si oui lesquelles choc avee un autre vehicule un carrefour. degats materiels mporfanfs - 3ntiers implique si applicable nometprenom karim gharbi vehicule peu.geot 308 adresse 20 rue des jasmins nature des dommages pare chocs avant h fjao.re 3o.uche 2074 la marsa tel. 95 654 324 montant estime 2 800 dt assureur star assurances n contrat 78945642 pieces jointes x constat amiable x photos i autres n immatriculation 423 men 4567 a fait a tunis le 42 / 05 2024 signature de l assure l iete anonyme au capital de 56 000 000 dt - r.c 6123456199 mf 1234567/a/m/000 de paris - 1001 tunis tet. 7 28 28 fax 71 28 28 29 ami assurances - """),
    ("devis","""s a devis maison deco n dv-2024-112 armensgemont renovotion date 18/0s/2024 chent ahmed ben solah adesso 45s rue de la liberte 1002 tunis t 98 123 456 designation montant ht peinture interieure - blanc corrotage soi - 60 60 moin d uvre 2700000 tva 19 4s6 000 total ttc 2 856 000 devis valable 30 jours maison deco amenagement renovation a"""),
    ("facture","""mega tronic societe de commarce facture rue de nindustito - 2035 charguis 1 tunio turidie . maf 1254ss1/a441000 n ft-2026-0568 toi 71 940 123 daze 20/0s/2024 client. ahmed ben saloh adresse 45 rue de la liberte 1002 tunis mf 1234567/b/av000 1250 00 70 00 120 00 smartphone samsung as4 chargeur rapide 2sv/ ecouteurs bluetooth arteteo 1 presente facture a la somme de haulle sept cent uelze dinars et soixante millimes. """),
    ("permis_conduire","""oio 70 - 07212629 i 4 t - 45 - - - - - 1 - . - - - . - pa - - - - p d t me - - - - ps - - - p - - s p . - - - - - . - 14 republique tumsienne r i w 3 .g - j - l ouw ub lrn mare du eterunce s vn 4 prememm date st e de naimance 6. namare de ta c arte etart ie natiocate adr t0 6 m ategories duie cc erilerance par extegorie io 1daie d echesace.per catc7 e d rasageme iu pertue lrau-iormes pues nuxdero e poriph etranget ou cu becyet euaaire l duq r l oplsisun a nembev de ptres d iree - la numer trdutif a ln gration des larpr snes du pertaie de contuirs. 4 5 - lx e permis de conouike l y 2l aies ls 22/109085 2015-03-13 4 f .. nauar 7 a r r 4. hedqami t . das p . c """),
    ("rapport_expertise","""expertise plus cobdinot d onpertise d assurances rapport d expertise exp.2024-0789 asaute ahmed ben solah date 16/0s/2024 n contrat 00123456 notute du sinistre accident de la ciccutation date du sinistre 12/0s/2024 lieu du sinistre tunis - avenue habib bourguiba 1. description nes dommages c un autre vehicule. nt. choc frontal ave degats importants suf la partie ava 2. evaluation des donmages desionation pare-chocs avant phare gauche moin d uvre 3 conclusion les dommages sont conseauilfs a le cout des reparotions est estim un accident ce lo circulation. a deux mille sept cent cinquante dinsrs. expert nabil kchoou expertise plus cotiner coupmense terguroncos signatute cachet """),
    ("declaration_sinistre", """l declaration de sinistre compagnie d assurance nord-est i numero de polce i 74 -8829-03 date du sinistre ay mars 2025 assure nom moreau jean-luc prenom ciean-luc adresse 27 tue des lilas 75044 fasis telephone 06 42 48 93 77 description du sinistre inondation dans le sous-sol suite vne rupture de toyauterie eau stagnante sur environ 45 m pendan g heures avant in ervenaion. ega4s constates sur le parc ue et les plinthes en bois. dommages estimes 2 450 pieces jointes photos jevis artisan facture pompe a eau signature et date a fait a paris le 46 marss 2025 c / l """)

]

# -----------------------------------------------------------------------
# 2. SYNTHETIC TEMPLATES — realistic vocabulary per class, with slot-fills
# -----------------------------------------------------------------------

FIRST_NAMES = ["Ahmed", "Mohamed", "Karim", "Sami", "Yassine", "Nadia", "Ines",
               "Sonia", "Walid", "Rania", "Amine", "Leila", "Hedi", "Faten"]
LAST_NAMES = ["Ben Salah", "Gharbi", "Trabelsi", "Cherni", "Bouazizi", "Jendoubi",
              "Khemiri", "Sassi", "Mejri", "Hamdi", "Bouzid", "Nasri"]
CITIES = ["Tunis", "Sfax", "Sousse", "Bizerte", "Nabeul", "Kairouan", "Gabes",
          "Ariana", "La Marsa", "Monastir"]
STREETS = ["Rue de la Liberté", "Avenue Habib Bourguiba", "Rue des Jasmins",
           "Rue de Carthage", "Avenue Mohamed V", "Rue Ibn Khaldoun"]
INSURERS = ["AMI Assurances", "STAR Assurances", "GAT Assurances", "Comar",
            "Lloyd Tunisien", "Assurances Maghrebia"]
CAR_BRANDS = [("PEUGEOT", "308"), ("RENAULT", "CLIO"), ("VOLKSWAGEN", "GOLF"),
              ("CITROEN", "C3"), ("HYUNDAI", "I10"), ("KIA", "PICANTO")]
COMPANIES = ["MEGA TRONIC", "MAISON & DECO", "TECH PLUS", "AUTO PIECES SFAX",
             "ELECTRO MENAGER TUNIS", "BATI CONSTRUCTION"]
EXPERT_CABINETS = ["EXPERTISE PLUS", "CABINET EXPERTAUTO", "AUTO EXPERT TUNISIE",
                    "EXPERTISE CENTRALE"]


def rand_date():
    d = random.randint(1, 28)
    m = random.randint(1, 12)
    y = random.randint(2023, 2026)
    return f"{d:02d}/{m:02d}/{y}"


def rand_contract():
    return "".join(str(random.randint(0, 9)) for _ in range(8))


def rand_plate():
    return f"{random.randint(100,999)} tunis {random.randint(1000,9999)}"


def rand_amount():
    return f"{random.randint(200, 5000)},{random.randint(0,99):02d}"


def rand_phone():
    return f"{random.randint(20,99)} {random.randint(100,999)} {random.randint(100,999)}"


def template_declaration():
    nom = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    tiers = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return f"""
DECLARATION DE SINISTRE
Assurances
Nom et Prenom : {nom}
Adresse : {random.randint(1,99)}, {random.choice(STREETS)}
{random.choice(CITIES)}
Tel : {rand_phone()}
Email : {nom.lower().replace(' ','.')}@email.tn
N Contrat : {rand_contract()}
Assureur : {random.choice(INSURERS)}
Date du sinistre : {rand_date()} Heure : {random.randint(0,23)}:{random.randint(0,59):02d}
Lieu du sinistre : {random.choice(STREETS)} {random.choice(CITIES)}
Nature du sinistre : Accident de la circulation
Circonstances detaillees :
Choc avec un autre vehicule a un carrefour. Degats materiels.
Tiers implique : {tiers}
Y a t il des blesses Non
Y a t il un constat amiable Oui
Fait a {random.choice(CITIES)} Le {rand_date()}
Signature de l assure
"""


def template_carte_grise():
    marque, type_ = random.choice(CAR_BRANDS)
    return f"""
REPUBLIQUE TUNISIENNE
MINISTERE DU TRANSPORT
CERTIFICAT D IMMATRICULATION
Immatriculation {rand_plate()}
Date de la premiere mise en circulation {rand_date()}
Marque {marque}
Type {type_}
Energie Essence
Puissance fiscale {random.randint(4,10)} CV
Nombre de places {random.randint(4,7)}
Usage Particulier
Numero d identification du vehicule VF{random.randint(1000000,9999999)}
Proprietaire {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}
Adresse {random.randint(1,99)}, {random.choice(STREETS)} {random.choice(CITIES)}
Le Ministre du Transport
"""


def template_permis():
    nom = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return f"""
REPUBLIQUE TUNISIENNE
MINISTERE DE L INTERIEUR
PERMIS DE CONDUIRE
Nom {nom}
Ne le {rand_date()} a {random.choice(CITIES)}
Adresse {random.randint(1,99)}, {random.choice(STREETS)} {random.choice(CITIES)}
Categorie B
Delivre le {rand_date()}
Valable jusqu au {rand_date()}
N de permis {random.randint(100000,999999)}
Autorite de delivrance {random.choice(CITIES)}
"""


def template_facture():
    societe = random.choice(COMPANIES)
    client = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    montant = rand_amount()
    return f"""
{societe}
Societe de Commerce
Rue de l Industrie {random.choice(CITIES)}
MF {random.randint(1000000,9999999)}/A/M/000
FACTURE
N FT-{random.randint(2023,2026)}-{random.randint(1000,9999)}
Date {rand_date()}
Client {client}
Adresse {random.randint(1,99)}, {random.choice(STREETS)} {random.choice(CITIES)}
Designation Qte PU HT Montant HT
Article {random.randint(1,5)} {rand_amount()} {montant}
Total HT {montant}
TVA 19 pourcent {rand_amount()}
Total TTC {montant}
Arretee la presente facture a la somme de
"""


def template_devis():
    societe = random.choice(COMPANIES)
    client = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return f"""
{societe}
Amenagement Renovation
DEVIS
N DV-{random.randint(2023,2026)}-{random.randint(100,999)}
Date {rand_date()}
Client {client}
Adresse {random.randint(1,99)}, {random.choice(STREETS)} {random.choice(CITIES)}
Designation Qte PU HT Montant HT
Peinture interieure {random.randint(10,80)} m2 {rand_amount()}
Main d oeuvre 1 {rand_amount()}
Total HT {rand_amount()}
TVA 19 pourcent {rand_amount()}
Total TTC {rand_amount()}
Devis valable 30 jours
"""


def template_constat():
    nomA = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    nomB = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    marqueA, typeA = random.choice(CAR_BRANDS)
    marqueB, typeB = random.choice(CAR_BRANDS)
    return f"""
constat amiable d accident automobile
Date de l accident {rand_date()} Lieu {random.choice(CITIES)}
Heure {random.randint(0,23)}:{random.randint(0,59):02d}
VEHICULE A CIRCONSTANCES VEHICULE B
Proprietaire assure {nomA} Proprietaire assure {nomB}
N Contrat {rand_contract()} N Contrat {rand_contract()}
Societe assurance {random.choice(INSURERS)} Societe assurance {random.choice(INSURERS)}
Vehicule Marque {marqueA} Vehicule Marque {marqueB}
Type {typeA} Type {typeB}
N immatriculation {rand_plate()} N immatriculation {rand_plate()}
Degats apparents Degats apparents
Pare-chocs avant Porte arriere droite
Signature des conducteurs
"""


def template_rapport_expertise():
    cabinet = random.choice(EXPERT_CABINETS)
    assure = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    return f"""
{cabinet}
Cabinet d expertise d assurances
RAPPORT D EXPERTISE
N EXP-{random.randint(2023,2026)}-{random.randint(100,999)}
Assure {assure}
N Contrat {rand_contract()}
Nature du sinistre Accident de la circulation
Date du sinistre {rand_date()}
Lieu du sinistre {random.choice(STREETS)} {random.choice(CITIES)}
Description des dommages
Choc frontal avec un autre vehicule Degats importants sur la partie avant
Evaluation des dommages
Designation Montant DT
Pare-chocs avant {rand_amount()}
Capot {rand_amount()}
TOTAL {rand_amount()}
Conclusion
Les dommages sont consecutifs a un accident de la circulation
Expert {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}
Signature et Cachet
"""


TEMPLATE_FUNCS = {
    "declaration_sinistre": template_declaration,
    "carte_grise": template_carte_grise,
    "permis_conduire": template_permis,
    "facture": template_facture,
    "devis": template_devis,
    "constat_amiable": template_constat,
    "rapport_expertise": template_rapport_expertise,
}


# -----------------------------------------------------------------------
# 3. NOISE INJECTION — mimic realistic OCR errors observed in your pipeline
# -----------------------------------------------------------------------

CONFUSIONS = {
    "o": "0", "O": "0", "l": "1", "S": "5", "s": "5", "B": "8",
}


def inject_noise(text: str, rate: float = 0.02) -> str:
    """Randomly swap a small fraction of characters to mimic OCR confusion,
    and occasionally drop a space or duplicate a character — matching the
    kinds of errors seen in real Tesseract output on these documents."""
    chars = list(text)
    for i in range(len(chars)):
        c = chars[i]
        if random.random() < rate:
            if c in CONFUSIONS and random.random() < 0.5:
                chars[i] = CONFUSIONS[c]
            elif c == " " and random.random() < 0.3:
                chars[i] = ""  # dropped space, e.g. "N Contrat"->"NContrat"
    return "".join(chars)





# -----------------------------------------------------------------------
# 5. BUILD DATASET
# -----------------------------------------------------------------------

def build_dataset(samples_per_class: int = 40):
    rows = []

    # Real samples first (cleaned same as production pipeline would)
    for label, raw in REAL_SAMPLES:
        rows.append((clean_text(raw), label))

    # Synthetic samples per class
    for label in LABELS:
        template_fn = TEMPLATE_FUNCS[label]
        for _ in range(samples_per_class):
            raw = template_fn()
            noisy = inject_noise(raw)
            rows.append((clean_text(noisy), label))

    random.shuffle(rows)
    return rows


def main():
    rows = build_dataset(samples_per_class=40)

    out_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "documents_dataset.csv")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    counts = {}
    for _, label in rows:
        counts[label] = counts.get(label, 0) + 1
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()