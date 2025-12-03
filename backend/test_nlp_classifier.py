from app.services.priority_classifier import NLPPriorityClassifier

def test_nlp_classifier():
    print("\n🤖 Testing NLP-Based Priority Classifier\n")
    print("="*70)
    
    classifier = NLPPriorityClassifier()
    

    # Test cases with different priorities
    test_cases = [
        {
            "title": "Victim receiving death threats from accused party",
            "description": "The victim and family are receiving continuous death threats. The accused has threatened to kill them. Immediate police protection is urgently needed as they fear for their lives.",
            "category": "life threat",
            "expected": "CRITICAL"
        },
        {
            "title": "Urgent medical treatment needed",
            "description": "Victim has severe injuries from the assault and requires immediate hospitalization. Medical emergency situation.",
            "category": "medical emergency",
            "expected": "HIGH"
        },
        {
            "title": "Compensation payment delayed",
            "description": "The compensation amount has not been credited to my bank account even after 60 days of case approval. Need to check status.",
            "category": "payment delay",
            "expected": "MEDIUM"
        },
        {
            "title": "Question about case status",
            "description": "I want to know the current status of my case and when I can expect an update.",
            "category": "general inquiry",
            "expected": "LOW"
        },
        {
            "title": "Violence and assault by upper caste members",
            "description": "I was physically assaulted and beaten. Need urgent police action against the perpetrators.",
            "category": "physical assault",
            "expected": "HIGH"
        },
        {
            "title": "Document verification pending",
            "description": "My caste certificate is still under verification for the past 3 weeks. Please expedite.",
            "category": "verification issue",
            "expected": "MEDIUM"
        }
    ]
    
    correct = 0
    
    for i, test in enumerate(test_cases, 1):
        result = classifier.classify_with_confidence(
            test['title'],
            test['description'],
            test['category']
        )
        
        is_correct = result['priority'] == test['expected']
        if is_correct:
            correct += 1
        
        print(f"\nTest {i}: {'✅' if is_correct else '❌'}")
        print(f"Title: {test['title']}")
        print(f"Expected: {test['expected']} | Got: {result['priority']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Explanation: {result['explanation']}")
        print("-"*70)
    
    accuracy = (correct / len(test_cases)) * 100
    print(f"\n📊 Accuracy: {accuracy:.1f}% ({correct}/{len(test_cases)} correct)")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_nlp_classifier()
