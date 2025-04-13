from typing import Dict, Any, List, Optional, Union


def calculate_score(input_data: Dict[str, Any], scorecard: Dict[str, Any], national_id) -> Dict[str, Any]:
    """
    Calculate a score based on input data and a scorecard configuration.
    
    Args:
        input_data: Dictionary containing input data for scoring
        scorecard: Dictionary containing the scorecard configuration
        
    Returns:
        Dictionary containing the calculated score, maximum possible score,
        missing attributes, and extra attributes
    """
    # Determine the settings dictionary based on the scorecard structure
    settings = scorecard.get('setting', scorecard)
    
    # Check if settings is empty or not a dictionary
    if not settings or not isinstance(settings, dict):
        return {
            "error": "Invalid scorecard format: scorecard data is empty or not a dictionary",
            "score": 0,
            "max_possible_score": 0,
            "missing_attributes": [],
            "extra_attributes": []
        }
    
    # Check if input_data is valid
    if not input_data or not isinstance(input_data, dict):
        return {
            "error": "Invalid input data: input data is empty or not a dictionary",
            "score": 0,
            "max_possible_score": 0,
            "missing_attributes": [],
            "extra_attributes": []
        }

        # Iterate through each attribute in the scorecard settings
    total_score = 0
    max_score = 0
    missing_attributes = []
    extra_attributes = []

    for attribute, settings in scorecard.items():
        attribute_type = settings['type']
        attribute_weight = int(settings['weight'])
        attribute_attributes = settings['attributes']
        attribute_value = input_data.get(attribute, None)
        
        if attribute_value is None or (isinstance(attribute_value, str) and attribute_value.strip() == ""):
            missing_attributes.append(attribute)
            continue
        
        try:
            attribute_value = int(attribute_value)
        except (ValueError, TypeError):
            # If conversion fails, log the error or handle it as needed
            pass

        base_score = 0  # Score before applying weight
        max_attribute_score = int(settings.get('maximum_score', 0))  # Default to 0 if not defined

        if attribute_type == 'rules':
            for rule in attribute_attributes[0]['rule']:
                condition = rule['condition']
                condition = condition.replace("value", "attribute_value")

                try:
                    if eval(condition, {'attribute_value': attribute_value}):
                        base_score = int(rule['score'])
                        break
                except Exception as e:
                    print(f"Invalid data encountered for attribute '{attribute}': {e}")
                    return {"error": "Data invalid"}

        elif attribute_type == 'string':
            valid_attribute = False
            for attr in attribute_attributes:
                if attr['key'] == attribute_value:
                    base_score = int(attr['score'])
                    valid_attribute = True
                    break
            if not valid_attribute:
                extra_attributes.append(attribute)

        # Compute weighted score and max weighted score
        weighted_score = base_score * attribute_weight
        max_weighted_score = max_attribute_score * attribute_weight

        total_score += min(weighted_score, max_weighted_score)
        max_score += max_weighted_score

    for attribute in input_data.keys():
        if attribute not in scorecard:
            extra_attributes.append(attribute)

    result = {
        "score": total_score,
        "max_score": max_score,
        "missing_attributes": missing_attributes if missing_attributes else None,
        "extra_attributes": extra_attributes if extra_attributes else None,
        "client_id": national_id
    }

    return result



def validate_scorecard(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the structure and content of a scorecard.
    
    Args:
        scorecard: The scorecard to validate
        
    Returns:
        Dictionary with validation results
    """
    errors = []
    
    # Check if scorecard has the required fields
    required_fields = ['id', 'version_id', 'decision_model_id', 'decision_type']
    for field in required_fields:
        if field not in scorecard:
            errors.append(f"Missing required field: {field}")
    
    # Determine the settings dictionary based on the scorecard structure
    settings = scorecard.get('setting', scorecard)
    
    # Check if settings is empty or not a dictionary
    if not settings or not isinstance(settings, dict):
        errors.append("Scorecard data is empty or not a dictionary")
        return {"valid": False, "errors": errors}
    
    # Validate each attribute
    for attribute, settings_data in settings.items():
        # Check if settings has the required fields
        attribute_required_fields = ['type', 'weight', 'attributes', 'maximum_score']
        for field in attribute_required_fields:
            if field not in settings_data:
                errors.append(f"Attribute '{attribute}' is missing required field: {field}")
        
        # Check if type is valid
        if 'type' in settings_data and settings_data['type'] not in ['rules', 'string']:
            errors.append(f"Attribute '{attribute}' has invalid type: {settings_data['type']}")
        
        # Check if attributes is a list
        if 'attributes' in settings_data and not isinstance(settings_data['attributes'], list):
            errors.append(f"Attribute '{attribute}' has invalid attributes (should be a list)")
        
        # For rules type, check if rule is properly formatted
        if 'type' in settings_data and settings_data['type'] == 'rules' and 'attributes' in settings_data:
            for attr_idx, attr in enumerate(settings_data['attributes']):
                if 'rule' not in attr:
                    errors.append(f"Attribute '{attribute}' rule {attr_idx} is missing 'rule' field")
                else:
                    for rule_idx, rule in enumerate(attr['rule']):
                        if 'condition' not in rule:
                            errors.append(f"Attribute '{attribute}' rule {attr_idx}.{rule_idx} is missing 'condition'")
                        if 'score' not in rule:
                            errors.append(f"Attribute '{attribute}' rule {attr_idx}.{rule_idx} is missing 'score'")
        
        # For string type, check if key-score pairs are properly formatted
        if 'type' in settings_data and settings_data['type'] == 'string' and 'attributes' in settings_data:
            for attr_idx, attr in enumerate(settings_data['attributes']):
                if 'key' not in attr:
                    errors.append(f"Attribute '{attribute}' option {attr_idx} is missing 'key'")
                if 'score' not in attr:
                    errors.append(f"Attribute '{attribute}' option {attr_idx} is missing 'score'")
    
    if errors:
        return {"valid": False, "errors": errors}
    else:
        return {"valid": True}


def get_scoring_matrix_decision(borrower_data, scorecard, scorecard_percentage_threshold, national_id):
    """
    Calculate a decision based on borrower data and scorecard criteria.
    
    Args:
        borrower_data: Dictionary containing borrower attribute values
        scorecard: Dictionary containing scoring criteria
        scorecard_percentage_threshold: Threshold percentage for approval
        national_id: Borrower's national ID
        
    Returns:
        Dictionary with total score, decision, and score breakdown
    """
    total_score = 0
    max_possible_score = 0
    breakdown = {}
    
    # Process each criterion in the scorecard
    for criterion, config in scorecard.items():
        weight = int(config["weight"])
        max_possible_score += weight
        
        # Get borrower's value for this criterion
        borrower_value = borrower_data.get(criterion, None)
        
        # Find matching attribute and get score
        score_value = 0
        try:
            criterion_type = config.get("type", "string")
            
            if criterion_type == "string":
                # String type - match against keys
                if borrower_value is not None:
                    for attribute in config["attributes"]:
                        if attribute["key"].lower() == str(borrower_value).lower():
                            score_value = int(attribute["score"])
                            break
                            
            elif criterion_type == "rules":
                # Rules type - evaluate conditions
                if borrower_value is not None:
                    # Convert borrower_value to numeric if possible for rule evaluation
                    try:
                        value = float(borrower_value)
                    except (ValueError, TypeError):
                        value = borrower_value
                    
                    # Process rules
                    for rule_set in config["attributes"]:
                        for condition in rule_set["rule"]:
                            # Handle the case where condition is simply 'true' (default case)
                            if condition.get("condition") is True:
                                score_value = int(condition["score"])
                                break
                                
                            # Otherwise evaluate the condition
                            try:
                                # Replace 'value' in condition with actual value
                                eval_condition = condition["condition"].replace("value", str(value))
                                if eval(eval_condition):
                                    score_value = int(condition["score"])
                                    break
                            except Exception as e:
                                print(f"Error evaluating rule condition: {e}")
                        
                        # If we found a matching condition in this rule set, we're done
                        if score_value > 0:
                            break
                    
        except Exception as e:
            print(f"Error processing attribute '{criterion}': {e}")
            continue
        
        # Calculate weighted score for this criterion
        criterion_score = score_value * weight / int(config["maximum_score"])
        
        # Add to total score
        total_score += criterion_score
        
        # Store details in breakdown
        breakdown[criterion] = {
            "raw_value": borrower_value,
            "score_value": score_value,
            "weight": weight,
            "weighted_score": criterion_score,
            "maximum_score": int(config["maximum_score"])
        }
    
    # Calculate score as percentage of maximum possible
    percentage_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
    
    # Determine decision threshold
    threshold = scorecard_percentage_threshold if scorecard_percentage_threshold else 80
    decision = "Approved" if percentage_score >= threshold else "Declined"
    
    return {
        "score": round(percentage_score, 2),
        "decision": decision,
        "total_score": round(total_score, 2),
        "max_possible_score": max_possible_score,
        "threshold": threshold,
        "breakdown": breakdown,
        "client_id": national_id
    }