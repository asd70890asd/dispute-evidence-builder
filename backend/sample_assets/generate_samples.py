import os
import json
from PIL import Image, ImageDraw


def generate_samples():
    """Generates the synthetic sample case assets and manifest."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base_dir, exist_ok=True)

    # 1. Write the text files
    txt_files = {
        "chat_leak.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "[2026-03-15 10:45 AM] Alex Morgan: Hi, I'm noticing a leak under the kitchen sink. Water is dripping onto the cabinet floor.\n"
            "[2026-03-16 09:15 AM] Northline Properties: Hello Alex. Thank you for reporting this. We will send someone to look at it this week."
        ),
        "plumber_receipt.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "FAST FIX PLUMBING\n"
            "Date: April 2, 2026\n"
            "Service Address: 1200 Fictional Ave, Toronto\n"
            "Customer: Northline Properties\n"
            "Services Rendered: Repaired leaking pipe joint under kitchen sink.\n"
            "Total Amount Due: $150.00\n"
            "Status: PAID IN FULL"
        ),
        "cleaning_receipt.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "SPOTLESS CLEANERS INC.\n"
            "Date: August 29, 2026\n"
            "Customer: Alex Morgan\n"
            "Address: 1200 Fictional Ave, Toronto\n"
            "Description: Deep cleaning of apartment unit prior to move-out.\n"
            "Total: $180.00\n"
            "Payment Method: Credit Card (PAID)"
        ),
        "deduction_letter.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "NORTHLINE PROPERTIES\n"
            "Date: September 5, 2026\n"
            "To: Alex Morgan\n"
            "Re: 1200 Fictional Ave, Toronto - Security Deposit Return\n\n"
            "Dear Alex,\n"
            "Upon inspection of the unit after your departure, we noted some damages requiring attention. "
            "Consequently, a total of $800.00 is being withheld from your deposit.\n"
            "Itemized deductions:\n"
            "- $500.00 for wall repainting due to water damage/staining.\n"
            "- $300.00 for professional unit cleaning.\n"
            "The remaining balance of your deposit has been transferred."
        ),
        "lease_excerpt.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "RESIDENTIAL LEASE AGREEMENT (EXCERPT)\n"
            "Date: September 1, 2025\n"
            "Landlord: Northline Properties\n"
            "Tenant: Alex Morgan\n"
            "Premises: 1200 Fictional Ave, Toronto\n\n"
            "Section 7: Maintenance and Repairs\n"
            "The Tenant shall keep the premises in good condition. The Tenant is not responsible for normal wear and tear resulting from ordinary use of the premises. Any damages beyond normal wear and tear caused by the Tenant will be deducted from the security deposit."
        ),
        "chat_dispute.txt": (
            "--- SYNTHETIC SAMPLE FICTIONAL DATA ---\n"
            "[2026-09-06 02:30 PM] Alex Morgan: I just received the deduction letter. I am disputing the $800.00 deduction. "
            "I already paid $180.00 for professional cleaning, so the $300 cleaning fee is unjustified.\n"
            "[2026-09-06 04:00 PM] Northline Properties: We will review our records and get back to you."
        )
    }

    for filename, content in txt_files.items():
        with open(os.path.join(base_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)

    # 2. Generate placeholder PNG files (clearly synthetic)
    png_specs = [
        ("movein_wall.png", "Move-in photo: living room wall"),
        ("moveout_stain.png", "Move-out photo: wall stain near window"),
    ]
    for filename, caption in png_specs:
        img = Image.new("RGB", (800, 600), color=(203, 213, 225))
        draw = ImageDraw.Draw(img)
        draw.text((240, 250), "SYNTHETIC SAMPLE", fill=(45, 55, 72))
        draw.text((200, 290), caption, fill=(74, 85, 104))
        draw.text((230, 320), "Fictional placeholder image", fill=(113, 128, 150))
        img.save(os.path.join(base_dir, filename))

    # 3. Create manifest.json
    manifest = [
        {"filename": "movein_wall.png", "kind": "photo", "date": "2025-09-01", "description": "Move-in photo: living room wall, no visible damage or stains."},
        {"filename": "chat_leak.txt", "kind": "chat_log", "date": "2026-03-15", "description": "Chat log: tenant reports a leak under the kitchen sink; landlord replies on 2026-03-16 saying someone will be sent this week."},
        {"filename": "plumber_receipt.txt", "kind": "receipt", "date": "2026-04-02", "description": "Plumber repair receipt: $150 for kitchen sink leak repair."},
        {"filename": "moveout_stain.png", "kind": "photo", "date": "2026-08-28", "description": "Move-out photo: faint discoloration mark on the bedroom wall near the window."},
        {"filename": "cleaning_receipt.txt", "kind": "receipt", "date": "2026-08-29", "description": "Professional cleaning receipt: $180, paid by tenant before move-out."},
        {"filename": "deduction_letter.txt", "kind": "document", "date": "2026-09-05", "description": "Landlord deduction letter: $800 withheld from deposit — $500 for wall repainting and $300 for cleaning."},
        {"filename": "lease_excerpt.txt", "kind": "document", "date": "2025-09-01", "description": "Lease excerpt: tenant is not responsible for normal wear and tear."},
        {"filename": "chat_dispute.txt", "kind": "chat_log", "date": "2026-09-06", "description": "Chat log: tenant disputes the $800 deduction and mentions the $180 cleaning receipt."}
    ]

    with open(os.path.join(base_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


if __name__ == "__main__":
    generate_samples()
    print("Sample assets generated.")
