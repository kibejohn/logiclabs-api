from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.schemas import ScoreCalculationRequest

from ..database import get_db
from ..models import User, Scorecard, ScorecardVersion, ScoreCalculation
from ..utils.auth import get_current_active_user
from ..services.calculate_scores import get_scoring_matrix_decision, calculate_score, validate_scorecard

router = APIRouter(
    prefix="/scoring",
    tags=["scoring"],
)

@router.post("/calculate")
def calculate_score_endpoint(
    request: ScoreCalculationRequest,
    scorecard_id: int,
    save: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate a score using the specified scorecard.
    
    Args:
        request: ScoreCalculationRequest containing input_data and nationalId
        scorecard_id: ID of the scorecard to use for calculation
        save: Whether to save the calculation to the database (default: True)
        
    Returns:
        Dictionary containing the calculated score and related information
    """
    input_data = request.input_data
    national_id = request.nationalId  # Optional: use this later when saving or logging
    
    # Get the scorecard
    scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to use this scorecard")
    
    # Get the latest version of the scorecard
    latest_version = db.query(ScorecardVersion).filter(
        ScorecardVersion.scorecard_id == scorecard_id
    ).order_by(ScorecardVersion.version_number.desc()).first()
    
    # Use the latest version data if available, otherwise use the scorecard data
    scorecard_data = latest_version.data if latest_version else scorecard.data
    scorecard_percentage_threshold = latest_version.percentage_threshold if latest_version else scorecard.percentage_threshold
    
    # Calculate the score
    if scorecard.decision_type == "scoring":
        result = calculate_score(input_data, scorecard_data, national_id)
        score_result = result["score"]
        max_score=result["max_score"]
        decision="Not Applicable",
        
    else:
        result = get_scoring_matrix_decision(input_data, scorecard_data, scorecard_percentage_threshold, national_id)
        score_result = result["total_score"]
        max_score=result["max_possible_score"]
        decision=result["decision"]

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    print("Score calculation result:", result)

    if save and national_id:
        calculation = ScoreCalculation(
            scorecard_id=scorecard_id,
            client_id=national_id,
            version_id=latest_version.id if latest_version else None,
            input_data=input_data,
            score_result=score_result,
            max_score=max_score,
            decision=decision,
            created_by_id=current_user.id
        )
        db.add(calculation)
        db.commit()
        print("Saved successfully")
    
    return result

@router.post("/validate-scorecard")
def validate_scorecard_endpoint(
    scorecard_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate a scorecard structure and content.
    
    Args:
        scorecard_data: Scorecard data to validate
        
    Returns:
        Dictionary containing validation results
    """
    validation_result = validate_scorecard(scorecard_data)
    
    if not validation_result["valid"]:
        return {"valid": False, "errors": validation_result["errors"]}
    
    return {"valid": True, "message": "Scorecard is valid"}

@router.get("/history")
def get_score_history(
    scorecard_id: int = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the score calculation history for the current user's business.
    """
    # Start building the query, joining with Scorecard to filter by business
    query = (
        db.query(ScoreCalculation)
        .join(Scorecard, ScoreCalculation.scorecard_id == Scorecard.id)
        .filter(Scorecard.business_id == current_user.business_id)
    )

    # Optional filter by scorecard_id
    if scorecard_id:
        query = query.filter(ScoreCalculation.scorecard_id == scorecard_id)

    # Order by creation date
    query = query.order_by(ScoreCalculation.created_at.desc())

    # Apply pagination
    calculations = query.offset(offset).limit(limit).all()

    # Prepare results
    results = []
    for calc in calculations:
        results.append({
            "id": calc.id,
            "scorecard_id": calc.scorecard_id,
            "client_id": calc.client_id,
            "decision": calc.decision or "Not Applicable",
            "scorecard_name": calc.scorecard.name if calc.scorecard else "Unknown Scorecard",
            "version_id": calc.version_id,
            "input_data": calc.input_data,
            "score_result": calc.score_result,
            "max_score": calc.max_score,
            "missing_attributes": calc.missing_attributes,
            "extra_attributes": calc.extra_attributes,
            "created_at": calc.created_at.isoformat() if calc.created_at else None,
        })

    return results


@router.get("/score/{score_id}")
def get_score_detail(
    score_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific score calculation.
    
    Args:
        score_id: ID of the score calculation to retrieve
        
    Returns:
        Score calculation details
    """
    # Get the score calculation
    calculation = db.query(ScoreCalculation).filter(ScoreCalculation.id == score_id).first()
    if calculation is None:
        raise HTTPException(status_code=404, detail="Score calculation not found")
    
    # Get the scorecard
    scorecard = db.query(Scorecard).filter(Scorecard.id == calculation.scorecard_id).first()
    if scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this score")
    
    # Format the result
    result = {
        "id": calculation.id,
        "scorecard_id": calculation.scorecard_id,
        "desision": calculation.decision,
        "scorecard_name": scorecard.name,
        "version_id": calculation.version_id,
        "input_data": calculation.input_data,
        "score_result": calculation.score_result,
        "max_score": calculation.max_score,
        "missing_attributes": calculation.missing_attributes,
        "extra_attributes": calculation.extra_attributes,
        "created_at": calculation.created_at.isoformat() if calculation.created_at else None
    }
    
    return result

@router.put("/score/{score_id}")
def update_score(
    score_id: int,
    input_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a score calculation with new input data.
    
    Args:
        score_id: ID of the score calculation to update
        input_data: New input data for the score calculation
        
    Returns:
        Updated score calculation details
    """
    # Get the score calculation
    calculation = db.query(ScoreCalculation).filter(ScoreCalculation.id == score_id).first()
    if calculation is None:
        raise HTTPException(status_code=404, detail="Score calculation not found")
    
    # Get the scorecard
    scorecard = db.query(Scorecard).filter(Scorecard.id == calculation.scorecard_id).first()
    if scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this score")
    
    # Get the latest version of the scorecard
    latest_version = db.query(ScorecardVersion).filter(
        ScorecardVersion.scorecard_id == calculation.scorecard_id
    ).order_by(ScorecardVersion.version_number.desc()).first()
    
    # Use the latest version data if available, otherwise use the scorecard data
    scorecard_data = latest_version.data if latest_version else scorecard.data
    
    # Calculate the new score
    result = calculate_score(input_data, scorecard_data)
    
    # Check if there's an error in the result
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Update the calculation
    calculation.input_data = input_data
    calculation.score_result = result["score"]
    calculation.max_score = result["max_score"]
    calculation.missing_attributes = result.get("missing_attributes")
    calculation.extra_attributes = result.get("extra_attributes")
    
    db.commit()
    
    # Format the result
    updated_result = {
        "id": calculation.id,
        "scorecard_id": calculation.scorecard_id,
        "scorecard_name": scorecard.name,
        "version_id": calculation.version_id,
        "input_data": calculation.input_data,
        "score_result": calculation.score_result,
        "max_score": calculation.max_score,
        "missing_attributes": calculation.missing_attributes,
        "extra_attributes": calculation.extra_attributes,
        "created_at": calculation.created_at.isoformat() if calculation.created_at else None
    }
    
    return updated_result