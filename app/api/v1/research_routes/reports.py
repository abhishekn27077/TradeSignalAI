from fastapi import APIRouter, Response

from app.research.report_generator import report_generator

router = APIRouter()

@router.get("/download/json", summary="Download Research Report (JSON)")
async def download_report_json():
    """
    Downloads the research metrics as a JSON file.
    """
    data = {"title": "Research Report", "accuracy": 68.5}
    json_data = report_generator.generate_json_report(data)
    
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=research_report.json"}
    )
    
@router.get("/download/pdf", summary="Download Research Report (PDF)")
async def download_report_pdf():
    """
    Downloads the research metrics as a PDF file.
    """
    data = {"title": "Research Report", "accuracy": 68.5}
    pdf_bytes = report_generator.generate_pdf_report(data)
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=research_report.pdf"}
    )
