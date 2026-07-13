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
    ("carte_grise","""58471236 ou ees enedu ype 3kpa3 a341a bme987 654 const ucte vols bla lols genre ioll yund hgn810p9z123456 type nstructur type commerciat 15 2022 accent oreate"""),
    ("carte_grise","""19 republique tunisien das 1oq certificat immatriculation jnaass dalg 05355012 on tou au serie du type activite dis 3kpa341 able283793 lola gore jluajl constructeur eco ma h9i4k461 pocontreme 533l 3jl type commercial 2070 07 07 dpaic rio 79"""),
    ("carte_grise","""republ ique tunisienne certificat imma triculation ueur 403 plaa aul9 noi et prenom bls uji 12 shgzan adresse 07335512 cncoumf gesd 55 55 serie du type gels llau 3kpa34 1able283793 lol genre sll elais constructeur hyunda h59a9k2 type constructeur elall 59 esui type commercial 2019 08 05 dpmc 631 jel accent sesnil 55"""),
    ("carte_grise","""republique tunisienne immatriculation serie du type vols blil syfbi urhebkp constructeur 676543 genre azoll toyota tabcd 1234567 8901 type constructeur prn type commercial corolla 20 05 2023 dem syj nom et prenom veleo 555 uxl 12 adresse 78945612 ou 98765432 oreate"""),
    ("constat_amiable", """constat amiable d accident automobile dute ge l acode-e 12 / 0s / 2024 love ueu tunis ticurose 14 30 tuunis - avenue habib bours bq mt p vemicutez 12 cinconstances t denicuce proes d eamserce / auare 3s 3 prores coaurarce l eract akmed ben safah commorc a noiee kacim gharbi n contat 00123456 foemura gas temtnte o r cotat 7834s612 o fcnemec ce 6e cecote u sootse d evnsance - ami assurances fextrerdos ocionce soutte jarurarce star assurances vencue tona 0 6ra mt a mucue feugeot. dornveut. vises renauct. type - 308 te -ctio n d ermaineuldon 123 uiys 4sgt n d mmatnculation 456 us t8io croquis de l accidont 12 cirecsao c orseras 1b degsts appurenes pare-chocs avant phare 3auck degats opparems porte arriere droite aile droite signature des conductours jh hhe u """),
    ("constat_amiable","""constat amiable d accident automobile ne cc nstn uc pas une reconnaissance de rcsponsabnhte. mais un releve a signer obligatoirement par les deux conducteurs des identites et des faits. servant a l acceleratton du reglement 1. date de l accident i heure 3. blesses meme legers 4. degats materiels autres s. temoins noms adresses et tel a soungner s il s agit dun passager de a ou b1 qu aux vehicules a et b k vehicule a 12. circonyances mehicule b i r mettre une croix x dans l m eqs - 6. societe d assurances chacune des cases utiles / 6. societe d assurances pour preciser le croquis vehicule assure par vehicule assure par .. en stationnement 1 1 a police d assurance n police d assurance n 2 quittalt un stationnement 2 i agence h agence attestation valable 3 prenalt un statlonnement 3 attestation valable . du au 7. identite du conducteur e 4 sortait d un parking d un lleu 4 prive d un chemin de terre du au 7. identite du conducteur 5 s engagealt dans un parking un 5 neu prive un chemin de terre nom nom p e e preno 6 arret de circulation 6 prenom ms adresse permis de conduire n 0 4 delivre le adresse 7 trotiement sans changement de file 7 permis de conduire n 8 heurtait a l arriere en roulant dans 8 le meme sens et sur une meme file y roulait dans le meme sens et s sur une fiie differente delivre le 8. assure voir attest. d assur. 8. assure voir attest. d assur. g 033f p e s t 10 changealt de file 10f nom 9 nom prenom 11 doublalt 11 prenom p adresse 12 virait a droite 12kl a adresse tel. 9. identite du vehicule marque type tfel. 13 virait a gauche 13 9. identite du vehicule marque type 14 reculait 14h- 15 empletait sur la partie de chaussee 15 reservee a la circulation en sens n d immatriculation n d immatriculation inverse sens suivi 16 venalt de droite dans un 16 sens suivi carrefour venant de 17 n avalt pas observe le signal 17 . a venant de de priorite allant a allant a iindiquer le nombre dee e ps - cases marquees d une croix 10. indiquer par une fleche estes dstque rs cune ctoux . rr 10 indiquer par une ecne le point de choc initial 13 croquis de i acmdent g ren le point de choc initial 77 l y n xt . . .it . 1 l i t 10 ..l- l l-4 - l- - ---.l i r- . l . l..- k - y z ga -w p wr litt kn su e e s p d 660 - .l- hjh 440 g i i 44 i r - t .-- ..-l l . .aa. -4 -e3- . a .l .4 - -.. - 14. observations 14. observahons u a 15 signature des conducteurs b cileil gase p-a5jl ol l h3l 4.jlule xiuaslf glel 53114 ug.ll enolall sll su lg sl ce 85 guao da us pallle ela mel 1 1 nb exigez une photocopie de l attestation internationale d assurances carte verte ou carte orange si le tiers est assure a l etranger. 11. degats apparents ll1. degats apparents . 4 de lgl tl a remplir par l assure et a transmettre dans les cinq jours a son assureur dans les 24 heures en cas de vol du vehicule . 1. nom de l assure 4s 1n profession le souscripteur n tel. 2. cil consigdcgs de qccident croquis seulement s il n a pas deja ete fait sur le constat au recto . designer les vehicules par a et b conformement au recto preciser 1. le trao6 des voles - 2 la direction des vehicules a b - 3. leur position au moment du choc - 4. les signaux routlers - 5 le nom des rues ou routes 3. a-t-il ete etabli un proces-verbale de la garde nationale un rapporl de polico si oui brigade ou poste de police a conducteur du vehicule assure est-il le conducteur habituel du vehicule .. ...... our non date de naissance ... o oi i oei i oo est-il salarie de l assure lou sinon a quel titre conduisait-il 5. vehicule assure lieu habituel de garage quel etait le inotif du deplacement expertise des degats garage ou le vehicule sera visible quand eventuellement telephoner a a ete vole indiquer son numero dans la serie du type voir carte grise l est gage nom et adresse de l organisme de credit l si le est un poids lourd poids total en charge vehicule etait attale a un autre vehicule tractant ou remorque au moment de l accident indiquer ie n d immaniculation de cet autre vehicuie . ppids total en charge nom de la societe qui l assue 1n police dans cette societe b. degals materiels autres qu aux vehicules a et b nature et importance nom et adresse du proprietaire 7. blesse s nom...... prenom et age adresse es .. profession.. . . . . . .. .ns0eere degre de parente avec l assure ou le conducteur.. ........ ... ... est-il salarie de l assure .. ... .... nature et gravite aes biessures.... situatlon au moment de l accident pleton passager du vehicule a ou b etc. 1 soins ou hospitalisation a..... 7 jar e p slgnature de l assure e """),
    ("constat_amiable","""constat amiable accident automobile dute de acode 12 2024 lave ueu tunis ticurose 14 30 tunis avenue habib boursu 12 cincoxstances proses aanrerce mose trass onttoe se les prerens euvrarce esmet akmed ben safah cormorc motase kacim gharbi cnumt 00123456 foemura eas tentote corta 7834sgi2 socese aveurance zami assurances soutte dorurance star assurances vencule tone 6aate mucue feuceot dorneut vtes renault type 308 tpe ctio ermainculton 123 4s6t unmatneulation 456 tt890 croquis de accidont 12 ctrecans onseras degsts appsrents pare chocs avant phare 3auck degats opparents porte arriere droite aile droite signature des conductours sre"""),
    ("constat_amiable","""s0j a555 aisla crv ghe constitue pas une reconnassance de ruspunsabdite mars un rolovo c63 dfenttes et fans sacvant faccotertion du degledent choyda 764 dato accidentto 24 wqu 202a houre al419 eets20 diss depats materuis autros quaux vohicules oull tomauns noms et adresse agt de passagers un veticule 58 616 305 vag 3s3 recisec duquet acub 14 en vjs mettre une crolx dans yat jels bynol chacune dos cases utiles lahat lun constat amiable accident automobile signer obligatoirement par les deux conducteurs vehicule rarlirepe de vges marque yype de immate oqh3 venant du alont vers dessa 50es 5205 70 dans meme vons rsi meme ph0iss surune sce ierente draver sratiocpreess 33 routat en sevrs nvorse iat assure voir attst assutance prenom le sour adesso les soue cesalge ftt provenat une cnaussse eiferente ftne 05516 sta assurances poice 205 aay00 32092 attest valabte du anj 93 aue nloer 81enwatonnemer ouerat starone conducteur voi porms de conduire dendaes prenor mawb adresse 112 mureeunre tep gss annacce vaes crrr permis de condurre detvre hoal lorst par la wilaya de teacss calegorie cdef fentourer categorie pas vrdreca 810 indiquer parune de choc initial 20y roulail en sens aterdk 21 tnobservatien un spnat de indiques le nombre de cases marquees une croix itis cins 53 nen madifier au constat apres separation des oxemplares"""),
    ("constat_amiable","""constat amiable accident automobile signer obligatoirement par les deux conducteurs date de laccident heure wocalisaton blessefs meme legertsh degeis materes 07 05 2024 44k30 avenue habib bourquiba tunis mon rmereraes objots autres fon oui crn vehicule 12 circonstances vehicule proncur assurancetassureporatesaondessamae tette crx 09 dars chacuno casosutes passu pour preciser le croquis preneur assurance assure vokr atlestation assuance nom ben abmed onstaionnemens aronte auitatunstationnomentsonraiune poriere nom trabelss prenom karinm 42 rue des jasmi pronaitun stationnoment prenom voussef aeresse 41 rue jasmrs sorat sunsitomement dulinapee adresso 45 rue de la liberte 4002 tunis un chemin de torce 4004 tunis pays tunisie awa uuh pays tunisie telouemar 98 423 456 rgagent srvne grisre tekouemai 97 654 324 vehicute routaitsurune placea sens giratoire vehicule heurtait arriero en routant dans le meme sons marque ype peugeot 208 il marque type renaule clio immatricutation 423 05 4567 190r en sers mts en immatriculation uup 10 changesxdoflo immatriculation 987 6543 pays immatriculation tan coubiait pays immatriculation tunrsie 12 viraita droite compagnie assurance voi attestaton assurance denomination astree assurances decontat 2024 42345 decarteverte 24 56789 attestation assurance carte verte vatable du 04 04 2024 20s 34 42 2024 13 viraitagauche 16 recuar denomination maghrebia assurances 18 empietait sur voio reservee la circulation en deconvat 2024 ma 98765 16 venait de droito dans carofour decartevene 24 14223 avait pas observe un ssgnal de priorite riige attestation assurance ou carte verte valabledu 46 02 2024 au 44 02 2025 compagnie assurance voir alestation asswancey indiquer le nombre de cases cochees 13 croquis de accident au moment du choe indiquer le trace des voies la direction des vehrcules conducteur vor permis de eonduire nom ben ahmed prenom karim conducteur vor pormis de conduie nom 7ra belsi eur position au moment du choc prenom youssef date de naissance 45 06 1390 rrs date de naissance 22 44 4988 adresse 42 rue des jasmirs 4002 tanis pays tunisie teloue mail 38 423 456 permis de conduire 42345628 defivre par tunis categorie valable jusqu au 45 06 2030 adresse 45 rue de la liberte 4004 tunis pays tunisie tel oue mai 97 654 324 permis de conduire 8765432 defivepar tunis categorie vatable jusqu au 22 44 7028 habib 30urju 14 mes observations le vehicule anjc de file sans 7h0 4hf et 14 mes observations le vehicule roulait ili vite et pas respecte la priorite au iratoire 15 signature des conducteurs fcrcufe barrer les mentions inutites"""),
    ("constat_amiable","""un relove teolemens teriets autros ules eus vehicule 12 societe auumncn assurances venicule axsure par aux vehie non elrconstances mettre une croix dans amt assnrmce checune des cases utiles polce assurance pour preciser croquie 245678 agence tuurs centre attestation valable 01 01 2024 societe assurances assurances vehicule assure par star assurances stationcement quettait un statonnement 31 12 2024 prensait un stationnement puall attestaton vaiable 12s ousraseupems 01 02 2024 au 34 01 2025 dentite au conducteur urs cherrin de tarre eerpgnaameupetre identite du conducteur parteng zteentite du conducteur prenom karim nom trabels engageat sur une sens gatore adresse 12 rue des jasmins prenom youssef 1002 tans rteiseumepmanne peuore meresso 45 ruc de la liberte pormis de condure 12345675 1004 tancs 1654 pelwele 15 06 2018 roueemimenmsen se pormes de consurs 87654324 en oeinre 22 14 2046 assure vor aesr omomcree assure voir attest assur nom ben ahmed soux prerom karim vanseote vom trabels vranaguomhe prenom youssef adresse 12 rue des jasmins recular adresse 45 rue de la liberte 1002 tans 15 emphetat surie parte de chansee 1001 tams 38 123 456 ce 16 ordation se 97 654 321 identite du vehicute 16 vanait de eroite dars un carretours identite du vehicule vehicule ldentite du vehicule marque type ugcot 208 17 mayantpes observe le prorite marque type renault clo immatnculaton 23 uxx 4567 bonomere decases cochees enmainoulation 987 6543 sens sum nord sud esa sons sum ouest est venantde rue de la liberte venantde avenue habib bourguiba alanta avenue habib bourg 13 croquis de accident allanta rue de la paix indiquer par une fleche pur point de choc inittai 11 degats apparents pore choc avant lt1 degats apparents porte arriere droite 5nl phare casse enfoncee 14 observations bservations 14 chanae de voie roulais normal le vehicu vehicule percute arriere sans ant 15 signature des conducteurs"""),
    ("constat_amiable","""ce 224qn2024 10h00 averue hefi nouia ariana rrrs dacfiers mlnl pes olh vemicule vtnm lore seciete sama asur eczecere vaprey nany ss6789 poue prsoes cuvon nou assuronces moghrebse reme enrosr beji234 stpctstue 2ut epeyeus uus sauste 00 en aeveutse catite mezn seetit pae den beisccem kms rue de independance oum umm que 002 66 avere de le bourse 2037 ariona mmou 1053 les berges du lac ce 20 03 2010 mremns suu 09 20is qeceut rrr frer fod vone vokswogen polo ford focus srz votkcwogen polo se 1ms sud nord 20 03 2024 mts vona ste ouwumemn rue de ariana sogoe mas 61n sogoe averve nouita avenue hed noutra 10 20 vre oue pre pare choc arriere gauche deforme se gesorveners cuis arrete au feu rouge pare choc avant droit grafle greenens pac le vehicule arreter tempc eyr"""),
    ("constat_amiable","""constat amiable ne constitue pas des identites et ccident automobile une reconnaissence de res des faits servant acp 25ab mais releve date de celeration du 42 06 iaccudem heure lieu dolemont signer obligatoirement par 102 les deux conducteurs 09h15 route de la marsa tunis diosses memotsgess degat materiels auts aux vehicules et res temoins etb rems adresses et tol souigens il agit un passagor khaled gharbi 22 345 628 scc cule 12 circonstances societe assurances mottre uno croix dons fam frentx aoub vehieule assure chacune des cases uti socie par utilos societe ami assurances pour preciser le eroquis curancez venicule assuse par star assurances poiice assurance ne 1254789 rionnecne agence tunis centre mmn tat un stationnement agence lae attestation walable rprenoit atationnomens atiestation vatable du 10 03 2024 au 09 03 somancrune purrchamie au 15 02 2024 au 14 02 2028 identite du conducteur chomis vom ben farhot 11 tere tdentite du conducteur en nom trabelsi premom yassine trattgonent sans changoment de adresse rue de ticurtait raniere en couait dons frenom mohamed rue de damas meme sons ou sur mecme adresso 45 hedi nouira idqa oulais dans la meme sens et sur une flo deltronte 4001 tunis permis de conduite 98765432 ehancoan fle pormis de conduire 87654324 53 eouvtat daiivreto 20 05 2016 delivre le 12 04 2018 12 virait eroito en assure voir attest assue assure voir attest assur 71 wisoit gauche nom ben farhat 14 vocveit dtom tabelsi 15 empietaicourta partiodo ehausese prenom mohamed prenom ym5an tesorvee circulation on sens adresse rue de damos 1002 tunis mverse adresse hedi nouira 4004 tunis 16 venait de droite jans un car 97 654 321 ta 98 765 432 47 avoi pas ebsorve sighal identite du vehicule eprorie idontite du vehicute hyundoi i10 andiquerie nombre de casos cochees marque typo renault clio un 43ai 4567 rimmatsiculation 987 6543 immatriculation 123 nord sud sons suna versmde cite wafa venant de cite wafa la marse la marsa 40 indiquer par une fleche ta point de choc initial 40 indiquer par une acche le point de choc initial 60 14 degets agga porte avant droite 41 degats apparents once aile avant enfoncee ragee 44 observations changeais de voie vehicule etait trop prache 44 observations roulais vehicule coupe la raufl 45 signature des conducteurs eptioll 3214l 00552 letranget 12a0 verte ou cante arange le diers est assuir rances n0rmalemenf"""),
    ("declaration_sinistre", """g2 en declaration de sinistre assurances l1jinformations sur l assureeb nometprenom ahmed ben salah adresso 5 rue de la liberte .1002 tunis t6 . 98 123 456 emoi ahmed.bensalah email.tn n convat 00f25 56 ls datedusnsue 12 / os / 2024 houre 14 30 leu avenue habib bour3uiba tunis noture dusinistre accident de la circulation circonstances getolliees choc avec un autre vehicule a un carrefour. degafs materiels importants. nometprenom karim gharbi tel 95 654 321 aasurance . star assui gaccs n convot 78945612 fota tunis le 12 / 05 / 2024 9 o we f / """),
    ("declaration_sinistre","""declaration de sinistre 0352419 assurances lis adresser dans les jours informations sur assure nom et prenom ahmed ben salah assureur ami assurances adresse 45 rue de la liberte agence tunis centre 1002 tunis tel 98 123 456 date effet du contrat 45 03 2023 email ahmed bensalah email 00123456 contrat iinformations sur le sinistre date du sinistre 42 05 2024 heure 44 30 ildesblesses doui non si oui nombre lieu du sinistre avenue habib bourquiba ilun constatamiable oui non si oui le joindre la presente declaration nature du sinistre accident de la circulation les autorites ont elles ete avisees ooui non circonstances detaillees si oui lesquelles choc avee un autre vehicule un carrefour degats materiels mporfanfs 13 atiers implique si applicable nom et prenom karim gharbi vehicule peugeo 308 20 rue des jasmi adresse 20 uia i4a ioimms nature des dommages pare chocs avant fjao uche tet 95 654 321 montant estime 800 assureur star assurances contrat 78945642 pieces jointes constat amiable photos autres immatriculation 423 4567 fait tunis le 42 05 2024 signature de assure iete anonyme au capital de 56 000 000 6123456199 1234567 000 avenue de paris 1001 tunis tet 71 28 28 28 fax 71 26 28 29 ami assurances siege soci"""),
    ("declaration_sinistre","""3nmia declaration de sinistre assurances l1tinformations sur assure nometprenom ahmed ben salah adresso rue de la liberte 1002 tunis tet 98 123 456 emoe ahmed bensalah email convat uui23 56 datedusinsue 12 2024 howe 14 30 leu aavenue habib bour3w tunis noture dusinistre accident de la circulation circonstances getolllees choc avec un autre vehicule un carrefour 3af materiels importants gintiers implique applicablesd nometprenom karim gharbi tel 95 654 321 assurance star assurances convot 78945612 fora tunis le 12 2024 olute"""),
    ("declaration_sinistre","""declaration de sinistre assurance nord est date de la dectaration 14 03 2025 numero de police 4471 8829 03 informations du client nom martin prenom sophie 27 vue des lilas 75011 paris adresse 42 18 93 77 telephone email soehie mar ema details du sinistre 12 03 2025 14h30 lieu garage souterrain 27 rue des lilas type de sinistre vol eer 0nn description sac main en quir noir contenant qorfe euil telephone gorfa ble iphone 14 et cles vole eendu stotionnement date du sinistre dommages estimes montant estime 850 pieces jointes proces verbal de depot de plainte 2025 031 0892 factures achat des objets voles photos du lieu du sinistre signature hie maroh fait paris le 14 mars 2025"""),
    ("declaration_sinistre","""declaration de sinistre compagnie assurance nord est police ne 2024 088317 42 rue des tilleuls 75011 paris tel 01 44 55 66 77 renseignements sur le sinistre date du sinistre 14 03 2024 heure approximative 19h45 lieu du sinistre 23 avenue du parc 35016 paris type de sinistre incendie deouts des eaux consecutifs description des dommages incendie declare dans la cuisine vers 19h45 propagetion limitee au placard dane remarent et et des trainr att plavie ine prari didi deut flatieig stratifie intervention des pompiers 20m2 eaaju utiisr pourl extinotirn andommage le nparquet cart evike ne djcent cloison platre aucun blesse i1l estimation preliminaire des dommages placard cuisine 450 plan de travail 320 parquet 280 cloison platre 180 total 230 00701 ete temoins intervenants pompiers paris 16 intervention 2024 0314 088 laurent dubois voisin 25 temom oculaire pieces jointes declaration des pompiers fait paris le 15 mars 2024 signature du declarant sophie marchand"""),
    ("declaration_sinistre","""declaration de sinistre compagnie assurance nord est numero de police 471 8829 03 date du sinistre mars 2025 assure nom moreau jean luc prenom ciean luc adresse 27 tue des lilas 750414 faris telephone 06 42 48 93 77 description du sinistre inondation dans le sous sol suite vne rupture de toyavterie eau stagnante sur environ 45 pendan heures avant ervenaion constates sur le pari et les plinthes en bois dommages estimes 450 pieces jointes photos jevis artisan facture pompe eau hociih porve 44111100 signature et date fait paris le 46 marss 2025"""),
    ("declaration_sinistre","""7 declaration de sinistre d assurance nord-est m compagnie date de la dectaration 14/03/2025 numero de police 4471-8829-03 l informations du client nom martin prenom sophie adresse 27 rue des lilas 25011 paris telephone q6 42 18 93 27 email soehie.mar n em l. y 1. details du sinistre 12/03/2025 a 14h30 lieu garage souterrain 27 rue des lilas type de sinistre vol d objet gersonnel description sac a main en cuir noir contenant orteleuille endant stotionnement. date du sinistre telephone gorfa.ble iphone 14 et cles vole p i. dommages estimes montant estime 4 850 iv. pieces jointes a proces-verbal de depot de plainte n 2025-031 4-0892 h factures d achat des objets voles k photos du lieu du sinistre v. signature so hie maroh fait a paris le 14 mars 2025 """),
    ("declaration_sinistre","""4 // //////// 72 - / c- es . e si c /i -ahy / f 4 g / 7 c00 peclaration de sinistre compaun e 0 a5 urance horo-est poice 4at1-8828-03 numero de jectaration 14 mars 2025 surle client // nom artin a prenem sophie 4 adresse 23 r des lilas 3501 paris /a telepmne q 42 18 93 33 / teiephone 06 nha l0 adefails du sinistre date aheure w i c l 3e souterrain 29 cue dm p e ekg4r oni lieu type de sinistre yol d g4yi portable macpook pro ma a ede dole itee tat pohe j4hoo0 date de la d description un ordinateur la c i -giace - uf a i en tait verrov une trace d e mc fon est visible spf le loz 7 i mais i //// montant estime des dommages l 8 30 // / t preces jointes 7 / e p o es-varbal de depot de pleinte e 2025 03hz-4471 e a facture g achat originale cr 50 photos des dogits 3 clches cn a ps m senature 01 declara / lo 44 mars 2025 fan a parie / 21 """),
    ("declaration_sinistre","""declaration de sinistre compagnie d assurance nord-est n police . ne-2024-088317 12 rue des tilleuls - 75011 paris tel ot 445566 77 1. renseignements sur le sinistre date du sinistre 14/03/2024 heure approximative 19h45 lieu du sinistre 23 avenue du parc 35016 paris type de sinistre incendie degats des eaux consecutifs l t f i1. description des dommages incendie declare dans la cuisine vers 19h45 propagetion limitee au placard dane remarent et et an des trainr att plavie ine prari didi deut flatieig ex stratifie. intervention des pompiers a 20m2.k eaaju utisr pourl extinotirn andommage le nparquet cart evike f d ne rr djcent cloison latre aucun blesse. il estimation preliminaire des dommages placard cuisine 450 plan de travail 320 parquet 3 m 280 cloison platre 180 total 1 230 iv. temoins / intervenants pompiers paris 16 intervention n 2024-0314-088 m. laurent dubois voisin n 25 temom oculaire / / a v. pieces jointes photographies des deaats g clich s declaration des pompiers devis fait a paris le 15 mars 2024 signature du declarant sophie marchand """),
    ("declaration_sinistre","""hmi declaration de sinistre n 0352419 assurances i q lis u a adresser dans les 5 jours 1 informations sur l assure nom et prenom ahmed ben salah assureur ami assurances adresse 45 rue de la liberte agence tunis centre 1002 tunis tel. 98 1423 456 date d effet du contrat 45/03/2023 email ahmed.bensalah email.tn 00123456 n contrat 2. informations sur le sinistre date du sinistre 42 7 05 7 2024 heure 44 30 ya-t-ildesblesses doui f non si oui nombre lieu du sinistre avenue habib bourquiba y a-t-il un constatamiable x oui non si oui le joindre a la presente declaration. nature du sinistre accidenf de la circulation les autorites ont-elles ete avisees oou k non circonstances detaillees si oui lesquelles choc avee un autre vehicule un carrefour. degats materiels mporfanfs - 3ntiers implique si applicable nometprenom karim gharbi vehicule peu.geot 308 adresse 20 rue des jasmins nature des dommages pare chocs avant h fjao.re 3o.uche 2074 la marsa tel. 95 654 324 montant estime 2 800 dt assureur star assurances n contrat 78945642 pieces jointes x constat amiable x photos i autres n immatriculation 423 men 4567 a fait a tunis le 42 / 05 2024 signature de l assure l iete anonyme au capital de 56 000 000 dt - r.c 6123456199 mf 1234567/a/m/000 de paris - 1001 tunis tet. 7 28 28 fax 71 28 28 29 ami assurances - """),
    ("devis","""s a devis maison deco n dv-2024-112 armensgemont renovotion date 18/0s/2024 chent ahmed ben solah adesso 45s rue de la liberte 1002 tunis t 98 123 456 designation montant ht peinture interieure - blanc corrotage soi - 60 60 moin d uvre 2700000 tva 19 4s6 000 total ttc 2 856 000 devis valable 30 jours maison deco amenagement renovation a"""),
    ("devis","""devis maison deco 2024 112 amensgemont renovotion date 18 2024 chent ahmed ben solah adesso 45s rue de la liberte 1002 tunis 98 123 456 montant peinture interieure blanc carrolage soi 60460 moin uvre 20000 tva 19 4s6 000 total ttc 856 000 devis valable 30 jours maison deco amenagement renovation"""),
    ("devis","""devis 2023 10 058 batiment solutions rue de la gare le 24 octobre 2023 75015 paris t6l 01 45 32 10 99 siret 450 789 123 00015 client client jean dubois 12 rue des fleurs 92100 boulogne billancourt prrumiare rour 2500 1625 00 425 00 485 00 910 00 total 20 total"""),
    ("devis","""en batimfnt solutions rue de gare 73015 puris t6l 014532 10 90 siret 450 799 123 00015 client nef servicles rpo1 igovauon complete salle de pto pemture saion couloir devis 2023 10 058 le 24 octobre 2023 client jean dubois 12 rue des fleurs 82100 bouiogne billancourt cicn zin 900 00 13 700 00 18 70 00 18 700 00 total 18 700 00 20 18 700 00 18 700 00"""),
    ("devis","""a5tisan du bois sfax pcudtiere 3002 sftrs tuniale tel 4216 74 245 789 fax 216 74 245 796 email contact artisandubois 1234s67va 000 devis 2024 076 client hedi ben ammar 15 avenue habib bourguiba 1001 tunis esigrton pocumtare oal tenrana 120x60 850 000 tnd 850 000 tnd ch08 fabrication chaises style scandinave chene finition vernis mat livraison signature du client sfas le 14 05 2024 pour artisan du bois sfax mansouri"""),
    ("devis","""jardins de tunisie devis 2024 01 091 ameragemant porsager date 25 janvier 2024 avenue hec chaker turss 1002 4216 71 234 567 1234567 000 client ahmed ben rue de la liberte la marsa 2070 upunmdeg 100 ammp 800 000 tnd mao3 installation systeme arrosage 450000 tnd 450 000 totalht 850 000 tnd tva 19 351 500 tho total 201 500 tnd tiou oreate"""),
    ("devis","""don ngaa son deco devis amena men renovation 275 date 20 05 2024 clent karim ben youssef adresse 12 avenue habab bourguiba 1001 tunis tel 98 765 432 mmium pemture intenioure blanc casse som 15 000 200 000 carrelage soi 60x60 45 238000 1710 00 pose de plaques de ptetre murs 30 28 000 840 000 electricite prise interrupteurs 15 pts 25 000 37500 main uvre s5000 550000 total en lettres trois muille six cent quarante six dinars tunisions 4375 000 tnd 831 250 tnd 206 250 tnd tva 19 totai ttc conditions de palement 30 la commande 70 la recepton des tavaux maison deco amenagement renovaton validite du devis 30 jours movesn 45 rue de ta lberte 1002 tures 98123456 contact manondeco ouve oreate"""),
    ("facture","""mega tronic societe de commarce facture rue de nindustito - 2035 charguis 1 tunio turidie . maf 1254ss1/a441000 n ft-2026-0568 toi 71 940 123 daze 20/0s/2024 client. ahmed ben saloh adresse 45 rue de la liberte 1002 tunis mf 1234567/b/av000 1250 00 70 00 120 00 smartphone samsung as4 chargeur rapide 2sv/ ecouteurs bluetooth arteteo 1 presente facture a la somme de haulle sept cent uelze dinars et soixante millimes. """),
    ("facture","""mememenenmns facture elec plus materiel electrique ne fac 2024 0421 date 15 05 2024 elec plus sarl echeance 14 06 2024 zone industrielle charguia 2035 ariana tunisie client tel 70 123 456 societe tunisienne de batiment emait contact elecplus rue de la liberte 1234567a 000 1002 tunis tunisie b1234567892016 9876543b 000 site web www elecplus b987654321201 ponqere prix unitaire tva 2078 cable electrique 3g2 100m total 120 000 19 600 000 disjoncteur differentiel 40a 30ma 85 000 850 000 prise de courant 16a interrupteur simple allumage boite encastrement goulotte pvc 40x60 arretee la presente facture la somme de mille neuf cent quatre vingt sept dinars et centquatre vingt mille sous total tva 19 conditions de paiement reglement par virement bancaire cachet et signature ou par cheque ordre de elec plus sarl elec plus sarl zone industriette charguia 2035 ariana tunisie 1234567a 000 tel 70 123 456 coordonnees bancaires banque de tunisie iban tn59 0001 2345 6789 1234 5678 swift btkntntt merci pour votre confiance"""),
    ("facture","""societe de commarce mega tronic rue de indusuto 2035 charguis tunio tunicle 1254ss1 am41000 2026 0568 toi 71 940 123 date 20 2024 client ahmed ben saloh adresse 45 rue de la liberte 1002 tunis 1234567 av000 smartphone samsung as4 chargeur rapide 2sv ecouteurs bluetooth avrteieo la presente facture la somme taule sept cent trelze dinars soixante millimes"""),
    ("facture","""facture bati pro fac 2024 0876 materiaux outillage date 22 05 2024 echeance 05 06 2024 bati pro sarl 15 rue des artisans 1002 tunis tunisie tel 71 234 567 email contact batipro 1234567a 000 b1234562018 site web www batipro designation quantite ciment portland 50kg 100 client societe generale de construction 45 avenue habib bourguiba 3000 sfax tunisie 9876543b 000 b98765432015 prix unitaire 1400 000 fer beton 12mm 1300 000 parpaing creux 20x20x40 550 000 sable de construction 10 40 000 400 000 gravier 38 000 304 000 peinture exterieure 20l 375 000 arretee la presente facture la somme de sous total 329 000 quatre mille cinq cent soixante seize dinars 823 110 tunisiens et soixante mille total ttc 152 110 conditions de paiement reglement par virement bancaire ou cheque ordre de bati pro sarl cachet et signature bati pro sarl 15 rue des artisans 1002 turus tunisie 1234567a 000 tel 71 234 567 coordonnees bancaires banque de tunisie iban tns9 0001 2345 6789 1234 5678 swift btkntntt merci pour votre confiance"""),
    ("facture","""facture fournitures eoa voee ormaatique fac 2024 031 date 28 04 2024 echeance 28 05 2024 mega fournitures sarl rue du lac leman ctient 1053 les berges du lac alpha services tunis tunisie rue lac victoria immeuble horzon 2eme etage tet 71862455 emait contact megafournitures 1425367a 000 817234562018 site web www megafournitures designation ramette papier 809 1002 turus tunisie 1234567b 000 b987654321014 stylo bille bleu boite de 50 150 000 classeur levier 30 sous total 2021 500 tva 19 383 545 total ttc 405 045 toner 85a 000000 cle usb 32gb arretee la presente facture la somme de deux mille quatre cent cinquante et un dinars tunisiens conditions de paiement reglement par virement bancaire ordre de mega fournitures sarl cachet et signature mega fournitures sarl rue du lac leman 1053 les berges du lac tunys tunisie tel 71862455 1425367a 000 coordonnees bancaires banque de tunisie iban tns9 0001 2345 6789 1234 5678 swift btkntntt merci pour votre confiance"""),
    ("facture","""facture fac 2024 0598 date 03 05 2024 echeance 02 06 2024 maison verte maison verte sarl rue ibn khaldoun 25 1002 turus tunisie client 71 808 600 hotel les oliviers emai contact maisonverte 1425367a 000 817234562019 site web maisonverte rue de ta plage sidi mahrez 4000 nabeul tunisie 9876543b 000 8b987654321098 prix unitaire quide vaissette ecolog 30 18500 19 nettoyant mutts surfaces 7s0ms 40 7200 19 288 000 lessive ecologique 5kg 22 000 19 550 000 desinfectant eucalyptus 20 92 800 19 196 000 sacs poubetle brodegradables ilot de 15 500 19 27 500 eponge vegetate lot de 10j 30 00 164 20 000 rrr se arretee la presente facture la somme de sous totat 1776 500 deux mille cinquante quatre dinars et sept cents mille tva 19 278 215 total ttc 2054 715 conditions de palement r99 afnenl per virement ban cachel gnature ordre de maison verte sarl maison verte sarl rue lbn ldoun 25 1002 tunis tunisie coord ordonnees bancaires 142536 000 banque de tunisie iban in59 0001 234 6789 1234 5678 tel 71 808600 swift btkntntt mercs pour votre confiance"""),
    ("facture","""froid tech facture climatisation froid industriel fac 2024 0672 date 10 06 2024 echeance 10 07 2024 froid tech sarl zone industrielle mghira 2082 ariana tunisie client tel 70 145 998 societe alimentaire wafa email contact froidtech rue de la manouba 1234567am 000 2010 la manouba tunisie b17234562017 9876543bm 000 site web www froidtech b987654321098 esses se total ttc 24 833 300 arretee la presente facture la somme de vingt trois mille quatre cent soixante dix dinars tunisiens conditions de paiement reglement par virement bancaire cachet et signature ordre de froid tech sarl froid tech sarl zone industrielle mghira coordonnees bancaires 2082 ariana tunisie 1234567am 000 banque de habitat agence ariana tel 70 145 998 iban tn59 0020 1234 5678 9012 3456 swift bhabtntt merci pour votre confiance"""),
    ("permis_conduire","""oio 70 - 07212629 i 4 t - 45 - - - - - 1 - . - - - . - pa - - - - p d t me - - - - ps - - - p - - s p . - - - - - . - 14 republique tumsienne r i w 3 .g - j - l ouw ub lrn mare du eterunce s vn 4 prememm date st e de naimance 6. namare de ta c arte etart ie natiocate adr t0 6 m ategories duie cc erilerance par extegorie io 1daie d echesace.per catc7 e d rasageme iu pertue lrau-iormes pues nuxdero e poriph etranget ou cu becyet euaaire l duq r l oplsisun a nembev de ptres d iree - la numer trdutif a ln gration des larpr snes du pertaie de contuirs. 4 5 - lx e permis de conouike l y 2l aies ls 22/109085 2015-03-13 4 f .. nauar 7 a r r 4. hedqami t . das p . c """),
    ("permis_conduire","""22 109085 2015 03 13 wueoamu 4al aaan 7un 199a 11 15 uxs 072142629 ma mrats dmsrunce vau fresem daze maimance namere le carte ieentiig netinnaty 44r00 alegories dute dellvrance par categocie 10 date echdsnce par aatec rie rentshtuete peruxte wan torme pate numero permme etranger beqvet enltalre oytaiue 84 netzhure de blres detiree 14 numarr retatif gratise des larprisnes du parvule de contaire 40 27 27 12 207e republiqt nisienne prrgro permis de conduire 334"""),
    ("permis_conduire","""remurlique tunisifnne 209 40 permis condutar 101 126360 bouid mokh tunis 210000 en me0sg vesmeete n00 emsumes 115115 940 rar yve ce evte cuu bace 12 08 1989 asi 00069630 numers de de cete un pva mance pes cuts gorte veeelsgrs vorure de optrotin"""),
    ("permis_conduire","""republique tunisienne 15 9ji 15ks 073 permis de conduire 01 547892 45 07 1970 ben ammar ahmed sfax 12 rue de la liberte sfax 1995 24 05 2010 25 05 20 06 1998 149 06 2013 40 11 2000 09 11 2015 633 commune desfax 12 42 2005 41 12 2020 ce teers wrii arund ahrire"""),
    ("permis_conduire","""republique tunisicnne 4255 scoor fermis de conduire 42 12 126360 12 08 1989 ben ahmed daal khaled 315 sousse au que 08 06 1975 00069660 vameie drv pegrit parscart kaarce cverueer priaeuer cat en ausature nuh aus vlrmciet niane pastenen drctis le dsdcvacu pao carscaree 19 lare ance ce descat carei preu perser parma arargre en baesa 403 nacure enty asxsn lles heureris ce hiques tommalle 51 prusde le 20 en petuie cae"""),
    ("permis_conduire","""republique tunisienne gel peraus de conduire 253l 14 07 1975 12 08 1999 sfax wjx ben salem es3 khalil 10 09 2015 00078912 00078910 25 rue de la liberte tunis 23 jiti nbhmh fait drictecces mas mnacn duce de enutance nurzro cara cacr2s naxcaccue alauc cdu mnc gra duclhh lcrx erncneess 11 dracrs pertea airacer de poru eass 42 2500 13 neste de nurrere de tlias 07e rmhma"""),
    ("permis_conduire","""republiquh tu iqie permis de conduire 45ly de permis date de delivrance 45 129834 2023 11 01 nom de delivrance ben salem prenom yassine yassine date et de nalssance carte identte 1998 05 20 sfax 09871234 adresse 14 rue habib bourguiba 3000 sfax categories bcde nemers permls condaire date de vrance nom prenorm date et ecu naimsece nemseee la carte elentite nallonaie admitd cotecorien date de edlivrance par caticdeis 10 date echiracs par cetecorie reccktions 32 persas tram orme pass samire permis etrascer du brevet aulitare natare de epleaion noentre de gtres deffvris syn imemtels tjh le grstiee rhh eiddsea perraa de condaire"""),
    ("rapport_expertise","""expertise plus cobdinot d onpertise d assurances rapport d expertise exp.2024-0789 asaute ahmed ben solah date 16/0s/2024 n contrat 00123456 notute du sinistre accident de la ciccutation date du sinistre 12/0s/2024 lieu du sinistre tunis - avenue habib bourguiba 1. description nes dommages c un autre vehicule. nt. choc frontal ave degats importants suf la partie ava 2. evaluation des donmages desionation pare-chocs avant phare gauche moin d uvre 3 conclusion les dommages sont conseauilfs a le cout des reparotions est estim un accident ce lo circulation. a deux mille sept cent cinquante dinsrs. expert nabil kchoou expertise plus cotiner coupmense terguroncos signatute cachet """),
    ("rapport_expertise","""expertise plus cabinet expertise ossurances rapport expertise exp 2024 0789 asaure ahmed ben solah date 16 2024 contrat 00123456 notute du sinistre accident de la circulation date du sinistre 12 2024 licu du sinistre tunis avenue habib bourguiba scrip on des dommages choc frontal avec un autre vehicu degats importants sur la partie avant evaluanion des dommages des onation pare chocs avant 800 000 capot 200 000 pharo gauche main uvre 300 000 total 750 000 conclusion les dommages sont conseanils un aocident de circulation le cout des reparations est estime deux mille sept cent cinquante dinars expert nabil kchoou cachet experti signature cache tdo lus ces"""),
    ("rapport_expertise","""rapporn exp 2024 0517 rapport expertise date 70672074 espert mandate cabret espertsos comeots expert hutiqr mastin adresse mnoourlp telephone 0478123456 ermai cortact arpertises comeds masion espertrie suite degbt des eaux date de la mistion 15 05 2024 ueu de la mission 12 rue des fleurt 69003 lyon demandeus assusrance securipro assure dupont jean de contrat 2023 09876 description des faits leclare avour constate une fuite eau le 14 05 2024 vers 22100 lommages au plafond et au muf du saton vtue en dessout tree dars le maur de la saile de ban assure provenant du puione de la sale de bain provoquant des nfiltratsons desd orgrne prevurnee de la fuite provrent une canalisation encas examen et constatations fuste eau confamee rovesu un raccord de canalisation salle de bain traces snurruote et aureoles sur le plafond et le ras du salon perture cloquee partiellement decoltee punthe en bois deformee par fhurmidite absence de veturte apparete anstallatons pretence eau stagnante au soi lors de lyiute origine du sinistre orgir sccidentelle due ta rupture dun raccord de canalsation encastree fuite eau repnie porcure plutord tuaion les dommages constates sont en ben direct avec la fuite eau survenue le 14 05 2024 le cout des reparations est estime 1560 00 ttc cette esaluation est valable pour une duree de mois compter la date du present rapport fait lyon 17 05 2024 lexpert jutien martun"""),
    ("rapport_expertise","""rapport exp 2024 0621 rapport expertise 21 06 2024 informations generales expert mandate cabinet expertises conseils expert lutien martin 23 rue de la republique 69002 lyon adresse telephone 04 78 12 34 56 email contact expenises conseils mission expertise suite degat des eaux date de la mission 20 06 2024 lieu de la mission 15 rue des tilleufs 69003 lyon demandeur assurance protect mme claire bemard assure de contrat prt 2024 112233 description des faits assuree declare avoir constate une fuite eau de la salle de bain provoquant des infiltrations le 19 06 2024 vers 18h30 provenant du plafond des dommages au plafond et au mur du salon situes en dessous origine presumee de la fuite provie une canalisation encastree dans le mur de la salle de bain examen et constatations fuite eau confirmee au niveau un raccord de canalisation salle de bain traces humidite et aureoles sur le plafond et le mur du salon peinture cloquee et partiellement decollee plinthe en bois deformee par humidite absence de vetuste apparente des installations presence eau stagnante au sol lors de la visite origine du sinistre fuite eau origine accidentelle due cause usure du materiel corrosion evaluation des dommages 12e reprise pemture mur salon surface 18 la rupture un raccord de canalisation encastree 418 00 342 00 98 00 210 00 longueur 10 intervention produit remplacement plinthe bois sechage et traitement anti moisissures divers imprevus 1148 00 tva 20 conclusion les dommages constates sont en lien direct avec la fuite eau survenue le 19 06 2024 le cout des reparations est estime 377 60 ttc cette evaluation est valable pour une duree de mois compter de la date du present rapport fait lyon le 21 06 2024 expert jutien martin annexes photos devis reparations eraniuie"""),
    ("rapport_expertise","""2024 0728 024 date 24 06 rapport expertis rapport informations generales erpert mandate cabinet expertises conseils expert julien martm 23 rue de la republique 69002 lyon 04 78 12 34 56 contact expertises conseils expertise suite degat des eaux mision 21 06 2024 de mission 12 avenue des tilleuls 69008 lyon nanu assurance protect mme ciaire bernard de contrat prt 2024 556677 description des faits assuree declare avoir constate de la cuisine provoquant des infi origie presumee de la fuite fuite eau le 21 06 2024 vers 17h30 provenant du plafond itratrons et des dommages au plafond et au mur adjacent rovient une canalisation encastree dans le mur de la cuisine examen et constatations fuite eau confirmee au niveau un raccord de canalisation cuisine traces humudite et aureoles sur le ptafond et le mur de la cuisine peinture cloquee et partiellement decollee plinthe en bois deformee par humidite absence de vetuste apparente des installations presence eau stagnante au sol fors de la visite origine du sinistre fuite eau origie accidentelle due cause usure du matenel corroston rupture un raccord de canalisation encastree evaluation des dommages eiii 879 00 1054 80 les dommages constates sont en lien direct avec la fuite eau surv enue le 21 06 2024 le cout des reparations est estime 054 80 ttc cette evaluation est valable pour une duree de mnois compter de la date du present rapport annexes fait lyon le 24 06 2024 expert julien martin photos devis reparations croquis oreate"""),
    ("rapport_expertise","""expertise plus cabinet expertise assurances rapport expertise exp 2024 0g9 assure sami trabelsi date 18 05 2024 contrat 00876543 nature du sinistre accident de la circulation date du sinistre 08 05 2024 lieu du sinistre tunis route de la marsa description des dommages collision avec un autre vehicule un carrefour degats materiels sur avant et le cote gauche du vehicule assure evaluation des dommages designation montant aile avant gauche 1350 000 phare avant gauche 650 000 500 000 350 000 conclusion les dommages sont consecutifs un accident de la circu atlo le cout des reparations est estime quatre mille trois cent cinquante cou expert nabil kohaou expertise plus cachet cabinet expertise assurances signature cacne 104 oreate"""),
    ("rapport_expertise","""expertise plus abi binet expertise assurances rapport expertise assure exp 2024 125g ania ben ali date contrat 00987654 lature du sinistre accident de la circulation date du sinistre 30 05 2024 lieu du sinistre sfax route de gabes description des dommages collision avec un autre vehicule un carrefour degats materiels sur avant et le cote droit du vehicule assure evaluation des dommages designation montant pare chocs avant 1200 000 1800 000 conclusion les dommages sont consecutifs un acclder dinars ime sept mille ce eparations est estime le cout des repar aile avant droite phare avant droit porte avant droite peinture et ajustements la circulation expert expertise plus n3bll kchaou cabinet expertise assyrances signature cachet oreate"""),
    ("rapport_expertise","""expertise plus abi binet expertise assurances rapport expertise assure exp 2024 125g ania ben ali date contrat 00987654 lature du sinistre accident de la circulation date du sinistre 30 05 2024 lieu du sinistre sfax route de gabes description des dommages collision avec un autre vehicule un carrefour degats materiels sur avant et le cote droit du vehicule assure evaluation des dommages designation montant pare chocs avant 1200 000 1800 000 conclusion les dommages sont consecutifs un acclder dinars ime sept mille ce eparations est estime le cout des repar aile avant droite phare avant droit porte avant droite peinture et ajustements la circulation expert expertise plus n3bll kchaou cabinet expertise assyrances signature cachet oreate"""),
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
    rows = build_dataset(samples_per_class=24)

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