from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.node import Node
from app.schemas.node import NodeHeartbeat, NodeResponse

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])


@router.post("/heartbeat", response_model=NodeResponse)
def heartbeat(payload: NodeHeartbeat, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    node = db.query(Node).filter(Node.node_id == payload.node_id).first()

    if node is None:
        node = Node(
            node_id=payload.node_id,
            hostname=payload.hostname,
            role=payload.role,
            site=payload.site,
            ip=payload.ip,
            status="online",
            created_at=now,
            updated_at=now,
            last_seen=now,
        )
        db.add(node)
    else:
        node.hostname = payload.hostname
        node.role = payload.role
        node.site = payload.site
        node.ip = payload.ip
        node.status = "online"
        node.updated_at = now
        node.last_seen = now

    db.commit()
    db.refresh(node)
    return node


@router.get("/", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(Node).order_by(Node.hostname).all()
