from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any, Union
import openai
import json
import uuid
import time
from datetime import datetime, timedelta

from app.models.knowledge_base import KnowledgeBase, KnowledgeQA, PresetQuestion
from app.models.knowledge_schemas import (
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeSearchRequest,
    KnowledgeQACreate, KnowledgeQAFeedback, PresetQuestionCreate
)
from app.models.user import User

class KnowledgeService:
    
    @staticmethod
    def create_knowledge_item(
        db: Session, 
        knowledge_data: KnowledgeBaseCreate, 
        user_id: int
    ) -> KnowledgeBase:
        """创建知识条目"""
        db_knowledge = KnowledgeBase(
            title=knowledge_data.title,
            content=knowledge_data.content,
            summary=knowledge_data.summary,
            source_file=knowledge_data.source_file,
            source_type=knowledge_data.source_type,
            tags=knowledge_data.tags,
            created_by=user_id
        )
        db.add(db_knowledge)
        db.commit()
        db.refresh(db_knowledge)
        return db_knowledge
    
    @staticmethod
    def create_knowledge_from_analysis(
        db: Session,
        title: str,
        content: str,
        analysis: str,
        source_file: str,
        user_id: int,
        tags: Optional[str] = None
    ) -> KnowledgeBase:
        """从文档分析结果创建知识条目"""
        # 生成摘要（取分析结果的前200字符）
        summary = analysis[:200] + "..." if len(analysis) > 200 else analysis
        
        # 自动提取标签
        if not tags:
            tags = KnowledgeService._extract_tags_from_content(content, analysis)
        
        knowledge_data = KnowledgeBaseCreate(
            title=title,
            content=content,
            summary=summary,
            source_file=source_file,
            source_type="document_analysis",
            tags=tags
        )
        
        return KnowledgeService.create_knowledge_item(db, knowledge_data, user_id)
    
    @staticmethod
    def _extract_tags_from_content(content: str, analysis: str) -> str:
        """从内容和分析中提取标签"""
        # 简单的关键词提取逻辑
        keywords = []
        
        # 常见企业相关关键词
        business_keywords = [
            "管理", "团队", "项目", "战略", "营销", "销售", "财务", "人力资源",
            "技术", "创新", "客户", "市场", "产品", "服务", "质量", "效率",
            "培训", "绩效", "流程", "制度", "文化", "领导力", "沟通", "协作"
        ]
        
        text = content + " " + analysis
        for keyword in business_keywords:
            if keyword in text:
                keywords.append(keyword)
        
        return ",".join(keywords[:5])  # 最多5个标签
    
    @staticmethod
    def get_knowledge_by_id(db: Session, knowledge_id: int) -> Optional[KnowledgeBase]:
        """根据ID获取知识条目"""
        knowledge = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_id,
            KnowledgeBase.is_active == True
        ).first()
        
        if knowledge:
            # 增加查看次数
            knowledge.view_count += 1
            db.commit()
        
        return knowledge
    
    @staticmethod
    def search_knowledge(
        db: Session, 
        search_request: KnowledgeSearchRequest
    ) -> Dict[str, Any]:
        """搜索知识库"""
        query = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True)
        
        # 关键词搜索
        if search_request.query and search_request.query.strip():
            search_term = f"%{search_request.query.strip()}%"
            query = query.filter(
                or_(
                    KnowledgeBase.title.ilike(search_term),
                    KnowledgeBase.content.ilike(search_term),
                    KnowledgeBase.summary.ilike(search_term),
                    KnowledgeBase.tags.ilike(search_term)
                )
            )
        
        # 标签筛选
        if search_request.tags:
            for tag in search_request.tags:
                query = query.filter(KnowledgeBase.tags.ilike(f"%{tag}%"))
        
        # 来源类型筛选
        if search_request.source_type:
            query = query.filter(KnowledgeBase.source_type == search_request.source_type)
        
        # 按相关性和创建时间排序
        query = query.order_by(desc(KnowledgeBase.view_count), desc(KnowledgeBase.created_at))
        
        total = query.count()
        items = query.limit(search_request.limit).all()
        
        return {
            "knowledge_items": items,
            "total": total,
            "query": search_request.query or ""
        }
    
    @staticmethod
    def ask_question(
        db: Session,
        question: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        is_guest: bool = False,
        knowledge_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """基于知识库回答问题"""
        start_time = time.time()
        
        # 构建上下文
        context_items = []
        used_knowledge_ids = []
        
        if knowledge_ids and len(knowledge_ids) > 0:
            # 使用指定的知识文档作为上下文
            specified_knowledge = db.query(KnowledgeBase).filter(
                KnowledgeBase.id.in_(knowledge_ids),
                KnowledgeBase.is_active == True
            ).all()
            
            for item in specified_knowledge:
                context_items.append(f"文档标题: {item.title}\n文档内容: {item.content}")
                used_knowledge_ids.append(item.id)
                
            if not context_items:
                # 如果指定的文档都无效，则进行搜索
                search_request = KnowledgeSearchRequest(
                    query=question,
                    limit=3
                )
                search_result = KnowledgeService.search_knowledge(db, search_request)
                
                for item in search_result["knowledge_items"]:
                    context_items.append(f"文档标题: {item.title}\n文档内容: {item.content[:800]}...")
                    used_knowledge_ids.append(item.id)
        else:
            # 搜索相关知识
            search_request = KnowledgeSearchRequest(
                query=question,
                limit=5
            )
            search_result = KnowledgeService.search_knowledge(db, search_request)
            
            for item in search_result["knowledge_items"]:
                context_items.append(f"文档标题: {item.title}\n文档内容: {item.content[:800]}...")
                used_knowledge_ids.append(item.id)
        
        context = "\n\n=== 分隔符 ===\n\n".join(context_items)
        
        # 使用OpenAI生成回答
        try:
            answer = KnowledgeService._generate_answer_with_openai(question, context, len(context_items))
        except Exception as e:
            answer = f"抱歉，我暂时无法回答这个问题。错误信息：{str(e)}"
        
        # 记录问答
        response_time = int((time.time() - start_time) * 1000)
        
        qa_record = KnowledgeQA(
            knowledge_id=used_knowledge_ids[0] if used_knowledge_ids else None,
            question=question,
            answer=answer,
            user_id=user_id,
            session_id=session_id or str(uuid.uuid4()),
            is_guest=is_guest,
            response_time=response_time
        )
        
        db.add(qa_record)
        db.commit()
        db.refresh(qa_record)
        
        return {
            "qa_id": qa_record.id,
            "question": question,
            "answer": answer,
            "related_knowledge": used_knowledge_ids,
            "response_time": response_time,
            "context_count": len(context_items)
        }
    
    @staticmethod
    def _generate_answer_with_openai(question: str, context: str, context_count: int = 1) -> str:
        """使用OpenAI生成回答"""
        if context_count > 1:
            system_prompt = f"""你是一个企业知识库助手。基于提供的{context_count}个相关文档内容回答用户问题。

规则：
1. 综合分析多个文档的信息，给出全面准确的回答
2. 如果多个文档有相关信息，请整合这些信息
3. 如果文档间有冲突信息，请指出并分别说明
4. 回答要条理清晰、重点突出
5. 使用中文回答
6. 在回答中可以适当注明信息来源（如"根据第一个文档"、"另一份资料显示"等）"""
        else:
            system_prompt = """你是一个企业知识库助手。基于提供的知识库内容回答用户问题。

规则：
1. 优先使用知识库中的信息回答
2. 如果知识库中没有相关信息，诚实地说明
3. 回答要简洁、准确、有帮助
4. 使用中文回答
5. 可以适当引用知识库中的具体内容"""

        user_prompt = f"""知识库内容：
{context}

用户问题：{question}

请基于上述知识库内容回答用户问题。"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {str(e)}")
    
    @staticmethod
    def get_preset_questions(db: Session, category: Optional[str] = None) -> List[PresetQuestion]:
        """获取预设问题"""
        query = db.query(PresetQuestion).filter(PresetQuestion.is_active == True)
        
        if category:
            query = query.filter(PresetQuestion.category == category)
        
        return query.order_by(PresetQuestion.order_index, PresetQuestion.created_at).all()
    
    @staticmethod
    def create_preset_question(
        db: Session, 
        question_data: PresetQuestionCreate
    ) -> PresetQuestion:
        """创建预设问题"""
        db_question = PresetQuestion(**question_data.dict())
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    
    @staticmethod
    def click_preset_question(db: Session, question_id: int) -> Optional[PresetQuestion]:
        """记录预设问题点击"""
        question = db.query(PresetQuestion).filter(PresetQuestion.id == question_id).first()
        if question:
            question.click_count += 1
            db.commit()
        return question
    
    @staticmethod
    def submit_feedback(
        db: Session,
        feedback_data: KnowledgeQAFeedback
    ) -> bool:
        """提交问答反馈"""
        qa_record = db.query(KnowledgeQA).filter(
            KnowledgeQA.id == feedback_data.qa_id
        ).first()
        
        if qa_record:
            qa_record.is_helpful = feedback_data.is_helpful
            qa_record.feedback = feedback_data.feedback
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_knowledge_stats(db: Session) -> Dict[str, Any]:
        """获取知识库统计信息"""
        total_knowledge = db.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True
        ).count()
        
        total_qa = db.query(KnowledgeQA).count()
        
        active_knowledge = db.query(KnowledgeBase).filter(
            KnowledgeBase.is_active == True,
            KnowledgeBase.view_count > 0
        ).count()
        
        # 获取热门标签
        popular_tags = []
        knowledge_items = db.query(KnowledgeBase.tags).filter(
            KnowledgeBase.is_active == True,
            KnowledgeBase.tags.isnot(None)
        ).all()
        
        tag_count = {}
        for item in knowledge_items:
            if item.tags:
                for tag in item.tags.split(','):
                    tag = tag.strip()
                    if tag:
                        tag_count[tag] = tag_count.get(tag, 0) + 1
        
        popular_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:5]
        popular_tags = [tag[0] for tag in popular_tags]
        
        # 获取最近问题
        recent_questions = db.query(KnowledgeQA.question).order_by(
            desc(KnowledgeQA.created_at)
        ).limit(5).all()
        recent_questions = [q.question for q in recent_questions]
        
        return {
            "total_knowledge": total_knowledge,
            "total_qa": total_qa,
            "active_knowledge": active_knowledge,
            "popular_tags": popular_tags,
            "recent_questions": recent_questions
        }
    
    @staticmethod
    def get_user_qa_history(
        db: Session,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        limit: int = 20
    ) -> List[KnowledgeQA]:
        """获取用户问答历史"""
        query = db.query(KnowledgeQA)
        
        if user_id:
            query = query.filter(KnowledgeQA.user_id == user_id)
        elif session_id:
            query = query.filter(KnowledgeQA.session_id == session_id)
        else:
            return []
        
        return query.order_by(desc(KnowledgeQA.created_at)).limit(limit).all()
    
    @staticmethod
    def init_preset_questions(db: Session) -> None:
        """初始化预设问题"""
        preset_questions = [
            {
                "question": "如何打造高效团队？",
                "category": "团队管理",
                "order_index": 1
            },
            {
                "question": "企业数字化转型的关键要素是什么？",
                "category": "数字化转型",
                "order_index": 2
            },
            {
                "question": "如何提升员工工作效率？",
                "category": "效率提升",
                "order_index": 3
            },
            {
                "question": "项目管理的最佳实践有哪些？",
                "category": "项目管理",
                "order_index": 4
            },
            {
                "question": "如何建立企业文化？",
                "category": "企业文化",
                "order_index": 5
            },
            {
                "question": "客户关系管理的核心策略？",
                "category": "客户管理",
                "order_index": 6
            },
            {
                "question": "如何进行有效的绩效考核？",
                "category": "绩效管理",
                "order_index": 7
            },
            {
                "question": "创新管理的方法和工具？",
                "category": "创新管理",
                "order_index": 8
            }
        ]
        
        # 检查是否已存在预设问题
        existing_count = db.query(PresetQuestion).count()
        if existing_count > 0:
            return
        
        # 批量创建预设问题
        for question_data in preset_questions:
            db_question = PresetQuestion(**question_data)
            db.add(db_question)
        
        db.commit() 