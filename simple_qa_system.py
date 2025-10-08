"""
Simplified Q&A System for Radiology Reports

Two-level questioning:
1. Category screening: "Are there any abnormalities in [category]?"
2. Specific questions: Only asked if category screening is positive
"""

def create_simple_questions_from_checklist(checklist):
    """Create simple 2-level questions from checklist"""
    
    questions = []
    
    # Skip non-clinical categories
    skip_categories = ["Initial Assessment", "Final Checks", "Image Quality"]
    
    for category in checklist['checklist']:
        category_name = category['category']
        
        # Skip procedural categories
        if any(skip in category_name for skip in skip_categories):
            continue
        
        # Level 1: Category screening question
        screening_q = {
            "level": 1,
            "type": "screening",
            "category": category_name,
            "question": f"Are there any abnormalities in the {category_name}?",
            "id": f"cat_{len(questions)}"
        }
        questions.append(screening_q)
        
        # Level 2: Specific questions for each subcategory
        for subcategory in category['subcategories']:
            subcat_name = subcategory['name']
            
            # Create specific questions from items
            for item in subcategory['items']:
                # Convert item to proper clinical question
                specific_q = convert_item_to_clinical_question(
                    item, category_name, subcat_name, screening_q['id']
                )
                if specific_q:
                    questions.append(specific_q)
    
    return questions

def convert_item_to_clinical_question(item, category, subcategory, depends_on_id):
    """Convert checklist item to proper clinical question"""
    
    item_lower = item.lower()
    
    # Skip procedural items
    skip_words = ['scroll', 'compare', 'review', 'check', 'assess', 'evaluate', 
                  'examine', 'look for', 'ensure', 'confirm']
    
    if any(word in item_lower for word in skip_words):
        # Convert procedural to clinical
        if 'trachea' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Is the trachea patent and normal in caliber?",
                "follow_up": "If abnormal, describe the location, size, and nature of the abnormality.",
                "depends_on": depends_on_id
            }
        elif 'effusion' in item_lower or 'pneumothorax' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Is there any pleural effusion or pneumothorax?",
                "follow_up": "If present, specify location, size (volume in ml or depth in cm), and characteristics.",
                "depends_on": depends_on_id
            }
        elif 'consolidation' in item_lower or 'masses' in item_lower or 'nodules' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Are there any consolidations, masses, or nodules?",
                "follow_up": "If present, specify location, size (in cm or mm), density, and characteristics.",
                "depends_on": depends_on_id
            }
        elif 'heart' in item_lower and 'size' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Is the heart size normal?",
                "follow_up": "If enlarged, specify cardiothoracic ratio and chamber involvement.",
                "depends_on": depends_on_id
            }
        elif 'aorta' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Is the aorta normal in size and appearance?",
                "follow_up": "If abnormal, specify location, diameter, and nature of abnormality (aneurysm/dissection).",
                "depends_on": depends_on_id
            }
        elif 'lymph' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Are there any enlarged lymph nodes?",
                "follow_up": "If present, specify location, size (short axis in mm), and stations involved.",
                "depends_on": depends_on_id
            }
        elif 'fracture' in item_lower:
            return {
                "level": 2,
                "type": "specific",
                "category": category,
                "subcategory": subcategory,
                "question": "Are there any bone fractures?",
                "follow_up": "If present, specify bones involved, location, and characteristics (displaced/non-displaced).",
                "depends_on": depends_on_id
            }
    
    # If we can't convert, return None (skip this item)
    return None

# Example usage
if __name__ == "__main__":
    import json
    
    # Example checklist
    example_checklist = {
        "checklist": [
            {
                "category": "Chest Structures",
                "subcategories": [
                    {
                        "name": "Airways",
                        "items": [
                            "Assess trachea for patency and caliber",
                            "Follow airways to segmental level",
                            "Look for endobronchial lesions"
                        ]
                    },
                    {
                        "name": "Pleura",
                        "items": [
                            "Look for effusion and pneumothorax",
                            "Assess density and loculation of effusion"
                        ]
                    }
                ]
            }
        ]
    }
    
    questions = create_simple_questions_from_checklist(example_checklist)
    
    print(f"Generated {len(questions)} questions:\n")
    for i, q in enumerate(questions, 1):
        print(f"{i}. [{q['type'].upper()}] {q['question']}")
        if q.get('follow_up'):
            print(f"   Follow-up: {q['follow_up']}")
        print()



