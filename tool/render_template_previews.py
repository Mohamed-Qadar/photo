"""Render every new design and one labeled contact sheet per category."""
from pathlib import Path
import sys
import json
import hashlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw
from photostudio.core import templates
from photostudio.core.pipeline import composite_preview
from photostudio.imaging.render import _load_font


def main():
    root = Path(sys.argv[1]) if len(sys.argv)>1 else Path("docs/template-previews")
    root.mkdir(parents=True, exist_ok=True)
    groups, manifest = {}, []
    for template in templates.NEW_TEMPLATES:
        image = Image.fromarray(composite_preview(templates.build(template), max_side=600), "RGBA")
        image.save(root/(template.key+".png"))
        groups.setdefault(template.category, []).append((template,image))
        manifest.append({"key": template.key, "name": template.name, "category": template.category,
                         "width": template.width, "height": template.height,
                         "sha256": hashlib.sha256(image.tobytes()).hexdigest()})
    for category, items in groups.items():
        sheet = Image.new("RGB", (1400, 1040), "#e9e9ed")
        draw = ImageDraw.Draw(sheet)
        for i,(template,image) in enumerate(items):
            x,y = (i%4)*350,(i//4)*520
            thumbnail = image.copy()
            thumbnail.thumbnail((326, 455), Image.Resampling.LANCZOS)
            sheet.paste(thumbnail, (x+(350-thumbnail.width)//2, y+10+(455-thumbnail.height)//2), thumbnail)
            draw.text((x+12,y+478), template.name, font=_load_font(16,True), fill="#17243b")
        name = category.split(" & ")[0].lower().replace(" ","-")
        sheet.save(root/("contact-"+name+".png"))
    (root/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(f"Rendered {len(manifest)} unique previews across {len(groups)} categories to {root}")


if __name__ == "__main__":
    main()
