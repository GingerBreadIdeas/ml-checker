import logging
from typing import Any, Dict, List, Optional

from bokeh.embed import file_html
from bokeh.layouts import column, row
from bokeh.models import (
    BooleanFilter,
    CDSView,
    Circle,
    ColumnDataSource,
    DataTable,
    HoverTool,
    MultiLine,
    TableColumn,
)
from bokeh.plotting import figure
from bokeh.resources import CDN
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import ChatMessage, User
from ..services.embeddings import create_embeddings, reduce_to_2d

logger = logging.getLogger(__name__)
router = APIRouter()


class MessageEmbeddingData(BaseModel):
    points: List[List[float]]
    messages: List[Dict[str, Any]]


@router.get("/message_embeddings_data")
def get_message_embeddings_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageEmbeddingData:
    """
    Return message embedding data as JSON for client-side visualization.

    Returns:
    - points: 2D coordinates for each message
    - messages: metadata for each message (id, content, date, etc.)
    """
    # Fetch messages for the current user
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .all()
    )

    if not messages:
        return {"points": [], "messages": []}

    # Extract text and metadata
    texts = [msg.content for msg in messages]

    # Create embeddings and reduce to 2D
    try:
        logger.info(f"Creating embeddings for {len(texts)} texts")

        # For debugging, limit the number of texts if there are many
        if len(texts) > 50:
            logger.warning(
                f"Limiting to 50 texts out of {len(texts)} for performance"
            )
            texts = texts[:50]

        embeddings = create_embeddings(texts)
        logger.info(
            f"Successfully created embeddings with shape {embeddings.shape}"
        )

        logger.info("Reducing embeddings to 2D with t-SNE")
        points_2d = reduce_to_2d(embeddings)
        logger.info(
            f"Successfully reduced embeddings to 2D with shape {points_2d.shape}"
        )
    except Exception as e:
        import traceback

        logger.error(f"Error generating embeddings: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error generating embeddings: {str(e)}"
        )

    # Convert numpy array to list of lists for JSON serialization
    points = [[float(x), float(y)] for x, y in points_2d]

    # Create message data
    message_data = [
        {
            "id": msg.id,
            "content": msg.content,
            "date": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_prompt_injection": msg.is_prompt_injection,
            "response": msg.response if msg.response else "",
        }
        for msg in messages
    ]

    return {"points": points, "messages": message_data}


# JSON endpoint for embedding visualization
@router.get("/message_embeddings_json")
def get_message_embeddings_json(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate a visualization of message embeddings in 2D as JSON for browser embedding.

    Returns JSON that can be embedded with Bokeh.embed.embed_item:
    - Regular messages displayed as blue dots
    - Prompt injection messages displayed as red dots
    - Interactive tooltips showing message details
    """
    import json

    from bokeh.embed import json_item

    # Fetch messages for the current user
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .all()
    )

    if not messages:
        return {"status": "empty", "message": "No messages found"}

    # Extract text and metadata
    texts = [msg.content for msg in messages]
    message_ids = [msg.id for msg in messages]
    created_dates = [
        msg.created_at.strftime("%Y-%m-%d %H:%M:%S") for msg in messages
    ]
    is_prompt_injection = [msg.is_prompt_injection for msg in messages]

    # Truncate long messages for the data table (preserve full text for hover)
    truncated_texts = []
    hover_texts = []
    for text in texts:
        # Truncate for table view
        trunc = text[:100] + "..." if len(text) > 100 else text
        truncated_texts.append(trunc)

        # Process for hover tooltip - escape special characters
        hover_text = text.replace("\n", " ").replace("\r", "")
        hover_text = (
            hover_text[:200] + "..." if len(hover_text) > 200 else hover_text
        )
        hover_texts.append(hover_text)

    # Create embeddings and reduce to 2D
    try:
        embeddings = create_embeddings(texts)
        points_2d = reduce_to_2d(embeddings)
    except Exception as e:
        import traceback

        logger = logging.getLogger(__name__)
        logger.error(f"Error generating embeddings: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

    # Prepare data for Bokeh
    source = ColumnDataSource(
        data={
            "x": points_2d[
                :, 0
            ].tolist(),  # Convert numpy values to Python native types
            "y": points_2d[:, 1].tolist(),
            "message_id": message_ids,
            "message": truncated_texts,  # For table display
            "hover_text": hover_texts,  # For hover tooltips
            "date": created_dates,
            "is_injection": is_prompt_injection,
            "color": [
                "#FF4136" if inj else "#0074D9" for inj in is_prompt_injection
            ],
            "size": [10 if inj else 8 for inj in is_prompt_injection],
        }
    )

    # Create plot with selection tools and sizing_mode for responsive behavior
    p = figure(
        title="Message Embeddings Visualization",
        tools="pan,wheel_zoom,box_zoom,reset,save,lasso_select,box_select",
        width=800,
        height=500,
        active_scroll="wheel_zoom",
        sizing_mode="stretch_width",  # Make plot stretch to container width
    )

    # Add hover tool with detailed tooltips
    hover = HoverTool(
        tooltips=[
            ("ID", "@message_id"),
            ("Message", "@hover_text{safe}"),
            ("Date", "@date"),
            ("Prompt Injection", "@is_injection"),
        ],
        point_policy="follow_mouse",
    )
    p.add_tools(hover)

    # Create circle renderers
    p.circle(
        "x",
        "y",
        source=source,
        size="size",
        fill_color="color",
        line_color="color",
        alpha=0.7,
        selection_color="firebrick",
        nonselection_alpha=0.3,
        selection_alpha=0.9,
    )

    # Configure legend with two color swatches
    from bokeh.models import Legend, LegendItem

    legend = Legend(
        items=[
            LegendItem(
                label="Regular Messages", renderers=[p.renderers[0]], index=0
            ),
            LegendItem(
                label="Prompt Injection", renderers=[p.renderers[0]], index=1
            ),
        ]
    )
    p.add_layout(legend, "right")

    # Create data table
    from bokeh.models import DataTable, StringFormatter, TableColumn

    columns = [
        TableColumn(field="message_id", title="ID", width=60),
        TableColumn(field="message", title="Message", width=400),
        TableColumn(field="date", title="Date", width=150),
        TableColumn(field="is_injection", title="Injection", width=80),
    ]

    data_table = DataTable(
        source=source,
        columns=columns,
        width=800,
        height=250,
        index_position=None,
        selectable=True,
        sortable=True,
        sizing_mode="stretch_width",  # Make table stretch to container width
    )

    # Create layout with both plot and table - make it responsive
    from bokeh.layouts import column

    layout = column(p, data_table, sizing_mode="stretch_width")

    # Convert the combined layout to a JSON item
    item_json = json_item(layout, "embedding-plot")

    return item_json


# Keep the HTML version for direct access if needed
@router.get("/message_embeddings", response_class=Response)
def get_message_embeddings_html(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Generate a visualization of message embeddings in 2D.

    Returns an HTML page with a Bokeh plot:
    - Regular messages displayed as blue dots
    - Prompt injection messages displayed as red dots
    - Interactive data table showing message content
    - Hovering over a point shows message details
    """
    # Fetch messages for the current user
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .all()
    )

    if not messages:
        return Response(
            content="<html><body><h1>No messages found</h1><p>Send some messages first to see visualizations.</p></body></html>",
            media_type="text/html",
        )

    # Extract text and metadata
    texts = [msg.content for msg in messages]
    message_ids = [msg.id for msg in messages]
    created_dates = [
        msg.created_at.strftime("%Y-%m-%d %H:%M:%S") for msg in messages
    ]
    is_prompt_injection = [msg.is_prompt_injection for msg in messages]

    # Create embeddings and reduce to 2D
    try:
        embeddings = create_embeddings(texts)
        points_2d = reduce_to_2d(embeddings)
    except Exception as e:
        return Response(
            content=f"<html><body><h1>Error generating embeddings</h1><p>{str(e)}</p></body></html>",
            media_type="text/html",
        )

    # Prepare data for Bokeh
    source = ColumnDataSource(
        data={
            "x": points_2d[:, 0],
            "y": points_2d[:, 1],
            "message_id": message_ids,
            "message": texts,
            "date": created_dates,
            "is_injection": is_prompt_injection,
            "color": [
                "#FF4136" if inj else "#0074D9" for inj in is_prompt_injection
            ],
            "size": [10 if inj else 8 for inj in is_prompt_injection],
        }
    )

    # Create plot
    p = figure(
        title="Message Embeddings Visualization",
        tools="pan,wheel_zoom,box_zoom,reset,save",
        width=800,
        height=600,
        active_scroll="wheel_zoom",
    )

    # Add hover tool
    hover = HoverTool(
        tooltips=[
            ("ID", "@message_id"),
            ("Message", "@message{safe}"),
            ("Date", "@date"),
            ("Prompt Injection", "@is_injection"),
        ],
        point_policy="follow_mouse",
    )
    p.add_tools(hover)

    # Create scatter plot for all points
    scatter = p.scatter(
        "x",
        "y",
        source=source,
        size="size",
        fill_color="color",
        line_color="color",
        alpha=0.7,
        legend_field="is_injection",
    )

    # Create views for regular and injection messages
    regular_filter = [not inj for inj in is_prompt_injection]
    injection_filter = is_prompt_injection

    regular_view = CDSView(
        source=source, filters=[BooleanFilter(regular_filter)]
    )
    injection_view = CDSView(
        source=source, filters=[BooleanFilter(injection_filter)]
    )

    # Add renderers for both groups
    p.circle(
        "x",
        "y",
        source=source,
        view=regular_view,
        size=8,
        color="#0074D9",
        alpha=0.7,
        legend_label="Regular Messages",
    )
    p.circle(
        "x",
        "y",
        source=source,
        view=injection_view,
        size=10,
        color="#FF4136",
        alpha=0.7,
        legend_label="Prompt Injection",
    )

    # Configure legend
    p.legend.location = "top_right"
    p.legend.click_policy = "hide"

    # Create data table
    columns = [
        TableColumn(field="message_id", title="ID", width=50),
        TableColumn(field="message", title="Message", width=350),
        TableColumn(field="date", title="Date", width=150),
        TableColumn(field="is_injection", title="Prompt Injection", width=100),
    ]

    data_table = DataTable(
        source=source,
        columns=columns,
        width=600,
        height=300,
        sortable=True,
        selectable=True,
        index_position=None,
    )

    # Create layout
    layout = column(
        p,
        data_table,
    )

    # Generate HTML
    html = file_html(layout, CDN, "Message Embeddings Visualization")

    return Response(content=html, media_type="text/html")
