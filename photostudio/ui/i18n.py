"""Offline English/Somali catalogue and live widget translation.

Stable document keys, user text, font names and filesystem paths are never translated.
"""
from PySide6.QtCore import QTranslator, QObject

LANGUAGE = "en"
SO = {
    "Big Sale Advert": "Xayeysiin iib weyn", "Shop Opening": "Furitaanka dukaan", "Service Promo": "Xayeysiin adeeg",
    "Business Card": "Kaarka ganacsiga", "Discount Story": "Sheeko qiimo-dhimis", "Phone Shop": "Dukaanka telefoonnada",
    "School Enrollment": "Diiwaangelinta iskuulka", "Study Tips": "Talooyin waxbarasho", "Exam Notice": "Ogeysiis imtixaan",
    "Library Event": "Munaasabadda maktabadda", "Restaurant Menu": "Liiska makhaayadda", "Daily Special": "Cuntada maanta",
    "Coffee Promo": "Xayeysiin qaxwo", "Delivery Offer": "Dalabka gaarsiinta", "Iftar Special": "Dalabka iftaarka",
    "Wedding Invite": "Casuumaadda arooska", "Conference": "Shirweyne", "Sports Day": "Maalinta ciyaaraha",
    "Charity Drive": "Ololaha sadaqada", "Eid Greeting": "Hambalyada ciidda", "Youth Meetup": "Kulanka dhallinyarada",
    "Announcement": "Ogeysiis",
    "Font family": "Nooca farta", "Gradient angle: ": "Xagasha midabka: ",
    "Could not create design": "Naqshadda lama samayn karin",
    "Ready": "Diyaar", "Unlock": "Fur qufulka", "Locked": "Qufulan", "Unlocked": "Furan", "Grouped": "Kooxaysan",
    "&File": "&Fayl", "&Edit": "&Tafatir", "&Image": "&Sawir", "&Insert": "&Ku dar",
    "&Arrange": "&Habee", "&Filter": "&Shaandhee", "&Beauty": "&Qurxin",
    "&Passport": "&Baasaboor", "&View": "&Muuqaal", "&Help": "&Caawin",
    "New Design": "Naqshad cusub", "Photo Editor": "Tafatiraha sawirrada",
    "Beauty Studio": "Qurxinta sawirrada", "Social Media Designer": "Naqshadaha baraha bulshada",
    "Graphic Design": "Naqshad garaafeed", "Custom Canvas": "Shiraac gaar ah",
    "Open Project": "Fur mashruuc", "Templates": "Naqshado diyaarsan",
    "Passport & ID Photo": "Sawirka baasaboorka iyo aqoonsiga",
    "Start creating": "Bilow abuurista", "Recent Projects": "Mashruucyadii dhawaa",
    "Blank canvas at any size.": "Shiraac bannaan oo cabbir kasta leh.",
    "Open a photo to crop, adjust & export.": "Fur sawir si aad u jarto, u hagaajiso una dhoofiso.",
    "Posts, stories, thumbnails with text & shapes.": "Qoraallo, sheekooyin iyo sawirro leh qoraal iyo qaabab.",
    "Posters, flyers, cards, banners, logos.": "Boorar, waraaqo xayeysiis, kaarar iyo astaamo.",
    "Pick exact width, height and DPI.": "Dooro ballaca, joogga iyo DPI-ga.",
    "Resume a saved .pstudio project.": "Sii wad mashruuc .pstudio oo kaydsan.",
    "20+ editable offline starter designs.": "In ka badan 20 naqshadood oo la tafatiri karo internet la'aan.",
    "Skin smoothing, spot removal, background blur.": "Jilcinta maqaarka, saarista dhibcaha iyo mugdinta asalka.",
    "Sizes, background swap, print sheets, PDF.": "Cabbirro, beddelka asalka, waraaqo daabacaad iyo PDF.",
    "A complete offline creative studio — design, edit and export, no account and no internet required.":
        "Xarun hal-abuur oo internet la'aan shaqaysa — naqshadee, tafatir oo dhoofi; akoon looma baahna.",
    "New Project…": "Mashruuc cusub…", "Open Image…": "Fur sawir…", "Open Project…": "Fur mashruuc…",
    "Import Image Layer…": "Ku dar lakab sawir…", "Replace Selected Image…": "Beddel sawirka la doortay…",
    "Import SVG…": "Ku dar SVG…", "Save Project": "Kaydi mashruuca",
    "Save Project As…": "Mashruuca ku kaydi magac…", "Export…": "Dhoofi…", "Home": "Bogga hore",
    "Exit": "Ka bax", "Undo": "Ka noqo", "Redo": "Dib u samee",
    "Crop (drag on canvas)": "Jar (jiid shiraaca)", "Rotate 90° CW": "U rog 90° midig",
    "Rotate 90° CCW": "U rog 90° bidix", "Flip Horizontal": "Rog dhinacyada",
    "Flip Vertical": "Rog kor iyo hoos", "Resize…": "Beddel cabbirka…", "Text": "Qoraal",
    "Rectangle": "Laydi", "Rounded Rectangle": "Laydi geeso wareegsan", "Ellipse": "Ugxan",
    "Triangle": "Saddex-xagal", "Line": "Xariiq", "Delete Layer": "Tirtir lakabka",
    "Align Left": "Ku sim bidix", "Align Center": "Ku sim bartamaha", "Align Right": "Ku sim midig",
    "Align Top": "Ku sim kore", "Align Middle": "Ku sim dhexda", "Align Bottom": "Ku sim hoose",
    "Bring Forward": "Hore u soo qaad", "Send Backward": "Gadaal u dir",
    "Duplicate Layer": "Nuqul ka samee lakabka", "Group Selected": "Kooxee kuwa la doortay",
    "Ungroup": "Kala fur kooxda", "Gaussian Blur": "Mugdi Gaussian", "Sharpen": "Afaynta sawirka",
    "Skin Smoothing": "Jilcinta maqaarka", "Portrait Enhance": "Hagaajinta wejiga",
    "Background Blur": "Mugdinta asalka", "Spot Removal (click skin)": "Saar dhibcaha (guji maqaarka)",
    "Replace Background…": "Beddel asalka…", "Create 10×15 cm Sheet": "Samee warqad 10×15 cm",
    "Create A4 Sheet": "Samee warqad A4", "Export PDF…": "Dhoofi PDF…",
    "Show Face Guides": "Muuji hagayaasha wejiga", "Zoom In": "Weynee", "Zoom Out": "Yaree",
    "Fit to Window": "La sim daaqadda", "Before session": "Kahor tafatirka",
    "Dark Theme": "Muuqaal madow", "Light Theme": "Muuqaal iftiin", "Settings…": "Dejinta…",
    "About": "Ku saabsan", "Settings": "Dejinta", "General": "Guud", "Language": "Luqadda",
    "English": "Ingiriisi", "Somali": "Soomaali", "Theme:": "Muuqaalka:",
    "Dark": "Madow", "Light": "Iftiin", "Properties": "Sifooyinka", "Layers": "Lakabyada",
    "Tools": "Qalabka", "Project": "Mashruuc", "Select / Move": "Dooro / Dhaqaaji", "Crop": "Jar",
    "Shape": "Qaab", "Image": "Sawir", "Background": "Asalka", "Rotate ↻": "U rog ↻",
    "Fit canvas": "La sim shiraaca", "Snapping": "Isku simid", "Adjustments": "Hagaajinta",
    "Exposure": "Soo-gaadhista iftiinka", "Brightness": "Iftiinka", "Contrast": "Kala duwanaanta",
    "Saturation": "Xoogga midabka", "Temperature": "Heerkulka midabka", "Grayscale": "Cawl",
    "Edit selected text": "Tafatir qoraalka la doortay", "Font size: ": "Cabbirka farta: ",
    "Text colour…": "Midabka qoraalka…", "Snap selected to canvas": "Ku sim kuwa la doortay shiraaca",
    "Bold": "Far culus", "Text outline: ": "Xadka qoraalka: ", "Shadow offset: ": "Fogaanta hooska: ",
    "Fill colour…": "Midabka gudaha…", "Stroke colour…": "Midabka xadka…", "Stroke: ": "Xadka: ",
    "Gradient fill…": "Midab kala guuraya…", "Transform": "Beddel muuqaalka", "Width": "Ballac",
    "Height": "Joog", "Rotation": "Wareeg", "Align to canvas": "Ku sim shiraaca",
    "Portrait tools": "Qalabka wejiga", "Spot radius: ": "Baaxadda dhibicda: ",
    "Reset adjustments": "Dib u celi hagaajinta", "Opacity": "Muuqashada", "Lock": "Quful",
    "Dup": "Nuqul", "Del": "Tirtir", "Rename": "Beddel magaca", "Lock / Unlock": "Quful / Fur",
    "Group selected": "Kooxee kuwa la doortay", "Duplicate": "Nuqul ka samee", "Delete": "Tirtir",
    "Duplicate selected": "Nuqul ka samee kuwa la doortay", "Delete selected": "Tirtir kuwa la doortay",
    "Add text": "Ku dar qoraal", "Add shape": "Ku dar qaab", "Add Text": "Ku dar qoraal",
    "Text:": "Qoraal:", "Edit text": "Tafatir qoraalka", "Resize": "Beddel cabbirka",
    "Width (px):": "Ballaca (px):", "Height (px):": "Joogga (px):", "Choose a canvas": "Dooro shiraac",
    "Social media preset:": "Cabbirka baraha bulshada:", "Graphic design preset:": "Cabbirka naqshadda:",
    "Open Image": "Fur sawir", "Import image layer": "Ku dar lakab sawir", "Replace image": "Beddel sawir",
    "Canvas background": "Asalka shiraaca", "Background colour": "Midabka asalka", "Import SVG": "Ku dar SVG",
    "Save Project As": "Mashruuca ku kaydi magac", "Export": "Dhoofi", "Export PDF": "Dhoofi PDF",
    "Unsaved changes": "Isbeddello aan kaydsanayn", "Save your changes before continuing?":
        "Ma kaydinaysaa isbeddellada ka hor intaadan sii wadin?", "Error": "Khalad",
    "Could not open image": "Sawirka lama furi karin", "Could not open project": "Mashruuca lama furi karin",
    "Could not save": "Lama kaydin karin", "Could not export": "Lama dhoofin karin",
    "Could not import image": "Sawirka lama soo gelin karin", "Could not import SVG": "SVG lama soo gelin karin",
    "Could not export PDF": "PDF lama dhoofin karin", "Could not create print sheet": "Warqadda daabacaadda lama samayn karin",
    "Project saved": "Mashruuca waa la kaydiyay", "Showing original (before)": "Sawirkii hore ayaa muuqda",
    "Showing edited (after)": "Sawirka la tafatiray ayaa muuqda", "Offline templates": "Naqshado internet la'aan",
    "Search name or category…": "Raadi magac ama qayb…", "Business": "Ganacsi", "Education": "Waxbarasho",
    "Restaurant": "Makhaayad", "Events": "Munaasabado", "Passport print layout": "Qaabka daabacaadda baasaboorka",
    "Example sizes only. Verify the dimensions, background and composition with the issuing authority.":
        "Cabbirradani waa tusaalooyin. Hay'adda bixisa ka hubi cabbirka, asalka iyo habaynta sawirka.",
    "Photo size": "Cabbirka sawirka", "Custom size": "Cabbir gaar ah", "Copies": "Nuqullo",
    "35 × 45 mm (common example)": "35 × 45 mm (tusaale caadi ah)",
    "50 × 50 mm (2×2 in example)": "50 × 50 mm (tusaale 2×2 in)", "40 × 60 mm (example)": "40 × 60 mm (tusaale)",
    "Gradient start": "Bilowga midab kala guurka", "Gradient end": "Dhammaadka midab kala guurka",
    "Save": "Kaydi", "&Save": "&Kaydi", "Discard": "Iska dhaaf", "&Discard": "&Iska dhaaf",
    "Cancel": "Jooji", "&Cancel": "&Jooji", "Open": "Fur", "&Open": "&Fur", "Close": "Xir",
    "&Close": "&Xir", "OK": "Haye", "Yes": "Haa", "No": "Maya",
    "Bring forward": "Hore u soo qaad", "Send backward": "Gadaal u dir",
    "Duplicate selected layers": "Nuqul ka samee lakabyada la doortay",
    "Delete selected layers": "Tirtir lakabyada la doortay", "Lock or unlock selected layers": "Quful ama fur lakabyada la doortay",
    "Approximate blur for centred portraits": "Mugdi qiyaas ah oo loogu talagalay wejiyada bartamaha yaal",
    "Effect strength; preserves facial geometry": "Xoogga saamaynta; qaabka wejiga waa la ilaaliyaa",
    "Snap to canvas and object edges; Space + drag to pan": "Ku sim shiraaca iyo geesaha walxaha; Space + jiid si aad u dhaqaajiso muuqaalka",
    "Recover project": "Soo celi mashruuc", "Recovery projects": "Mashruucyada soo kabashada",
    "Choose a recovery project:": "Dooro mashruuc la soo celinayo:", "No recent projects": "Mashruucyo dhowaan la furay ma jiraan",
    "Saving…": "Waa la kaydinayaa…", "Exporting…": "Waa la dhoofinayaa…",
    "left": "bidix", "center": "bartamaha", "right": "midig", "rectangle": "laydi",
    "rounded": "geeso wareegsan", "ellipse": "ugxan", "triangle": "saddex-xagal", "line": "xariiq",
    "Preparing print sheet… Export the finished sheet as PDF.": "Warqadda daabacaadda ayaa la diyaarinayaa… Marka ay dhammaato u dhoofi PDF.",
    "Click a blemish to remove it (toggle off when done)": "Guji dhibic si aad u saarto (dami marka aad dhammayso)",
    "Crop: drag a rectangle on the canvas (Esc to cancel)": "Jar: ku jiid laydi shiraaca (Esc si loo joojiyo)",
    "An image operation is still running. Please wait.": "Hawl sawir ayaa weli socota. Fadlan sug.",
    "Image operation discarded because the document changed.": "Hawshii sawirka waa la joojiyay sababtoo ah mashruucu wuu isbeddelay.",
    "Unlock the background layer before changing its colour.": "Fur qufulka lakabka asalka ka hor beddelka midabkiisa.",
    "Transform Selection": "Beddel kuwa la doortay", "Move Selection": "Dhaqaaji kuwa la doortay",
    "Delete Selection": "Tirtir kuwa la doortay", "Duplicate Selection": "Nuqul ka samee kuwa la doortay",
    "Reorder Layers": "Habee kala horraynta lakabyada", "Set Opacity": "Deji muuqashada",
    "Lock Layer": "Quful lakabka", "Unlock Layer": "Fur lakabka", "Show Layer": "Muuji lakabka",
    "Hide Layer": "Qari lakabka", "Add Text": "Ku dar qoraal", "Add Shape": "Ku dar qaab",
    "Add Image": "Ku dar sawir", "Edit Text": "Tafatir qoraalka", "Rotate 90°": "U rog 90°",
    "Move Layer": "Dhaqaaji lakabka", "Group": "Kooxee", "Canvas Background": "Asalka shiraaca",
    "Replace Image": "Beddel sawirka", "Replace Background": "Beddel asalka", "Spot Removal": "Saar dhibcaha",
    "Image/canvas dimensions must be positive and at most 40 megapixels":
        "Cabbirrada sawirka ama shiraaca waa inay togan yihiin, kana badnaan 40 megapixel.",
    "Physical dimensions and DPI must be positive": "Cabbirrada jireed iyo DPI waa inay togan yihiin.",
    "The photo does not fit inside the sheet margins": "Sawirku kuma dhex habboona xuduudaha warqadda.",
    "DPI must be positive": "DPI waa inuu togan yahay.",
}

SNIPPETS = {
    "62 editable offline designs across 11 categories.": "62 naqshadood oo internet la'aan ah, kuna kala jira 11 qaybood.",
    "Football & Sports": "Kubadda cagta iyo ciyaaraha",
    "Business & Marketing": "Ganacsiga iyo suuqgeynta",
    "Ramadan & Islamic Holidays": "Ramadaan iyo ciidaha Islaamka",
    "Weddings & Celebrations": "Aroosyada iyo dabaaldegyada",
    "Education & Books": "Waxbarashada iyo buugaagta",
    "Announcements & Civic Information": "Ogeysiisyada iyo xogta bulshada",
    "Digital Content": "Nuxurka dhijitaalka ah",
    "All categories": "Dhammaan qaybaha",
    "Use Template": "Isticmaal naqshadda",
    "Rendering preview…": "Samaynta horudhaca…",
    "No matching templates": "Ma jiraan naqshado ku habboon",
    "Double-click text to edit. Click a photo to replace it. Drag to move.": "Laba jeer guji qoraalka si aad u beddesho. Guji sawirka si aad u beddesho. Jiid si aad u dhaqaajiso.",
    "Solid color": "Midab keliya", "Gradient": "Midab kala guuraya",
    "Start color…": "Midabka bilowga…", "End color…": "Midabka dhammaadka…",
    "Bring Forward": "Hore u keen", "Send Backward": "Gadaal u dir", "Edit": "Wax ka beddel",
    "Remove Watermark…": "Ka saar calaamadda biyaha…",
    "Export Preview…": "Horudhaca dhoofinta…",
    "Export Preview": "Horudhaca dhoofinta",
    "Rendering export preview…": "Samaynta horudhaca dhoofinta…",
    "Export preview includes the watermark unless a valid license is active.": "Horudhaca dhoofinta waxaa ku jira calaamadda biyaha haddii ruqsad sax ahi aanay shaqaynayn.",
    "Version ": "Nooca ", "Developed by ": "Waxaa sameeyay ",
    "Computer Engineer": "Injineer kombiyuutar", "specializing in ": "ku takhasusay ",
    "Specializing in ": "Ku takhasusay ",
    "Natural Language Processing and Computer Vision": "Farsamaynta luqadda dabiiciga ah iyo aragga kombiyuutarka",
    "Offline-first photo &amp; design studio.": "Xarun sawirro iyo naqshado oo internet la'aan shaqaysa.",
    "offline-first photo &amp; design studio.": "xarun sawirro iyo naqshado oo internet la'aan shaqaysa.",
    "In active development.": "Weli waa la horumarinayaa.", "Contact:": "Xiriir:",
    "NLP & Computer Vision": "NLP iyo aragga kombiyuutarka",
}


def source_text(value):
    exact = next((source for source, translated in SO.items() if translated == value), None)
    if exact is not None:
        return exact
    for source, translated in SNIPPETS.items():
        value = value.replace(translated, source)
    return value


def tr(text):
    text = str(text)
    if LANGUAGE != "so":
        return text
    if text in SO:
        return SO[text]
    if text.startswith("Adjust "):
        return "Hagaaji " + tr(text[7:].capitalize())
    for prefix, translated in [("Undo ", "Ka noqo "), ("Redo ", "Dib u samee "),
                               ("Exported ", "Waa la dhoofiyay "), ("Zoom ", "Weyneynta "),
                               ("Sheet capacity: ", "Awoodda warqadda: ")]:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            return translated + (tr(rest) if prefix in ("Undo ", "Redo ") else rest.replace("photos", "sawirro"))
    for source, translated in SNIPPETS.items():
        text = text.replace(source, translated)
    return text


class CatalogueTranslator(QTranslator):
    def isEmpty(self):
        return False

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        return SO.get(sourceText, "") if LANGUAGE == "so" else ""


def set_language(language):
    global LANGUAGE
    LANGUAGE = language if language in ("en", "so") else "en"


def retranslate(root):
    """Retain source strings as widget metadata; switching never touches documents."""
    from PySide6.QtWidgets import (QLabel, QAbstractButton, QGroupBox, QLineEdit,
                                  QComboBox, QFontComboBox, QTabWidget, QDockWidget, QToolBar)
    from PySide6.QtGui import QAction
    for widget in [root] + root.findChildren(QObject):
        properties = []
        if isinstance(widget, (QLabel, QAbstractButton, QAction)): properties.append(("text", "setText"))
        if isinstance(widget, QGroupBox): properties.append(("title", "setTitle"))
        if isinstance(widget, QLineEdit): properties.append(("placeholderText", "setPlaceholderText"))
        if isinstance(widget, (QDockWidget, QToolBar)): properties.append(("windowTitle", "setWindowTitle"))
        properties.append(("toolTip", "setToolTip"))
        if hasattr(widget, "prefix"): properties.append(("prefix", "setPrefix"))
        blocked = widget.blockSignals(True)
        for getter, setter in properties:
            if not hasattr(widget, getter): continue
            key = "translation_" + getter
            value = getattr(widget, getter)()
            if not value: continue
            source = widget.property(key)
            if source is None:
                source = source_text(value)
                widget.setProperty(key, source)
            getattr(widget, setter)(tr(source))
        if isinstance(widget, QComboBox) and not isinstance(widget, QFontComboBox):
            for i in range(widget.count()):
                source = widget.itemData(i, 257) or source_text(widget.itemText(i))
                widget.setItemData(i, source, 257)
                widget.setItemText(i, tr(source))
        if isinstance(widget, QTabWidget):
            for i in range(widget.count()):
                page = widget.widget(i)
                source = page.property("translation_tab") or source_text(widget.tabText(i))
                page.setProperty("translation_tab", source)
                widget.setTabText(i, tr(source))
        widget.blockSignals(blocked)
