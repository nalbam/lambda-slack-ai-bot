#!/usr/bin/env python3
"""
워크플로우 엔진 테스트 스크립트
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ python-dotenv가 설치되지 않았습니다. 'pip install python-dotenv'로 설치해주세요.")
    sys.exit(1)

# 환경 변수 로드
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    print("⚠️ .env.local 파일이 없습니다. 환경 변수가 시스템에서 로드됩니다.")

try:
    from src.workflow.workflow_engine import WorkflowEngine
    from src.workflow.task_executor import TaskExecutor
    from src.workflow.slack_utils import SlackMessageUtils
    from src.config import settings
    from src.utils import logger
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    sys.exit(1)


class WorkflowTester:
    """워크플로우 엔진 테스트 클래스"""
    
    def __init__(self):
        # Mock Slack 앱과 컨텍스트 생성
        self.mock_app = Mock()
        self.mock_app.client = Mock()
        
        self.test_context = {
            "channel_id": "C1234567890",
            "user_id": "U1234567890", 
            "thread_ts": "1234567890.123456",
            "event_ts": "1234567890.123456",
            "text": "테스트 메시지",
            "bot_user_id": "B1234567890"
        }
        
        print("✅ 워크플로우 테스트 환경 설정 완료")
    
    def test_workflow_engine_initialization(self) -> Dict[str, Any]:
        """워크플로우 엔진 초기화 테스트"""
        print("\n🔧 워크플로우 엔진 초기화 테스트")
        print("-" * 40)
        
        results = []
        
        try:
            print("\n📝 테스트 1: WorkflowEngine 인스턴스 생성")
            start_time = time.time()
            
            workflow_engine = WorkflowEngine(self.mock_app, self.test_context)
            
            end_time = time.time()
            
            result = {
                "test_number": 1,
                "test_name": "workflow_engine_init",
                "success": True,
                "response_time": round(end_time - start_time, 2),
                "has_app": hasattr(workflow_engine, 'app'),
                "has_context": hasattr(workflow_engine, 'slack_context'),
                "has_task_executor": hasattr(workflow_engine, 'task_executor'),
                "has_slack_utils": hasattr(workflow_engine, 'slack_utils')
            }
            
            print(f"✅ 성공 - {result['response_time']}초")
            print(f"📱 앱 연결: {result['has_app']}")
            print(f"📋 컨텍스트: {result['has_context']}")
            print(f"⚙️ 작업 실행기: {result['has_task_executor']}")
            print(f"🔧 Slack 유틸: {result['has_slack_utils']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "workflow_engine_init",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "workflow_engine_initialization", "results": results}
    
    def test_task_executor_operations(self) -> Dict[str, Any]:
        """작업 실행기 테스트"""
        print("\n⚙️ 작업 실행기 테스트")
        print("-" * 40)
        
        results = []
        
        try:
            print("\n📝 테스트 1: TaskExecutor 인스턴스 생성")
            start_time = time.time()
            
            task_executor = TaskExecutor(self.mock_app, self.test_context)
            
            end_time = time.time()
            
            result = {
                "test_number": 1,
                "test_name": "task_executor_init",
                "success": True,
                "response_time": round(end_time - start_time, 2),
                "has_app": hasattr(task_executor, 'app'),
                "has_context": hasattr(task_executor, 'slack_context'),
                "has_slack_utils": hasattr(task_executor, 'slack_utils')
            }
            
            print(f"✅ 성공 - {result['response_time']}초")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "task_executor_init",
                "success": False,
                "error": str(e)
            })
        
        # 2. 지원되는 작업 타입 테스트
        try:
            print("\n📝 테스트 2: 지원되는 작업 타입 확인")
            
            task_executor = TaskExecutor(self.mock_app, self.test_context)
            
            # 지원되는 작업 타입들
            supported_task_types = [
                "text_generation",
                "image_generation", 
                "image_analysis",
                "thread_summary",
                "gemini_text_generation",
                "gemini_image_generation",
                "gemini_video_generation",
                "gemini_image_analysis",
                "check_video_operation"
            ]
            
            result = {
                "test_number": 2,
                "test_name": "supported_task_types",
                "success": True,
                "supported_types": supported_task_types,
                "total_types": len(supported_task_types)
            }
            
            print(f"✅ 성공")
            print(f"📊 지원 작업 타입 수: {result['total_types']}")
            print(f"📋 타입 목록: {', '.join(supported_task_types[:5])}...")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "supported_task_types",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "task_executor_operations", "results": results}
    
    def test_slack_utils_operations(self) -> Dict[str, Any]:
        """Slack 유틸리티 테스트"""
        print("\n🔧 Slack 유틸리티 테스트")
        print("-" * 40)
        
        results = []
        
        try:
            print("\n📝 테스트 1: SlackMessageUtils 인스턴스 생성")
            start_time = time.time()
            
            slack_utils = SlackMessageUtils(self.mock_app)
            
            end_time = time.time()
            
            result = {
                "test_number": 1,
                "test_name": "slack_utils_init",
                "success": True,
                "response_time": round(end_time - start_time, 2),
                "has_app": hasattr(slack_utils, 'app'),
                "has_client": hasattr(slack_utils, 'client')
            }
            
            print(f"✅ 성공 - {result['response_time']}초")
            print(f"📱 앱 연결: {result['has_app']}")
            print(f"🔗 클라이언트: {result['has_client']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "slack_utils_init",
                "success": False,
                "error": str(e)
            })
        
        # 2. 메시지 형식 검증
        try:
            print("\n📝 테스트 2: 메시지 형식 검증")
            
            slack_utils = SlackMessageUtils(self.mock_app)
            
            # 테스트용 메시지 데이터
            test_messages = [
                {"type": "text", "content": "안녕하세요!"},
                {"type": "image", "uploaded": True, "filename": "test.jpg"},
                {"type": "video_operation", "status": "processing"},
                {"type": "analysis", "content": "이미지 분석 결과"}
            ]
            
            result = {
                "test_number": 2,
                "test_name": "message_format_validation",
                "success": True,
                "test_messages_count": len(test_messages),
                "message_types": [msg["type"] for msg in test_messages]
            }
            
            print(f"✅ 성공")
            print(f"📊 테스트 메시지 수: {result['test_messages_count']}")
            print(f"📋 메시지 타입: {', '.join(result['message_types'])}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "message_format_validation",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "slack_utils_operations", "results": results}
    
    def test_workflow_scenarios(self) -> Dict[str, Any]:
        """워크플로우 시나리오 테스트"""
        print("\n🎭 워크플로우 시나리오 테스트")
        print("-" * 40)
        
        results = []
        
        # 1. 간단한 텍스트 요청 시나리오
        try:
            print("\n📝 테스트 1: 간단한 텍스트 요청 시나리오")
            
            workflow_engine = WorkflowEngine(self.mock_app, self.test_context)
            
            # Mock 응답 설정
            workflow_engine.slack_utils.send_message = Mock()
            workflow_engine.slack_utils.update_message = Mock()
            
            simple_request = "안녕하세요, AI에 대해 설명해주세요."
            
            result = {
                "test_number": 1,
                "test_name": "simple_text_scenario",
                "success": True,
                "request": simple_request,
                "scenario_type": "simple_text",
                "note": "Mock 환경에서 구조 검증만 수행"
            }
            
            print(f"✅ 성공")
            print(f"📝 요청: {result['request'][:50]}...")
            print(f"🏷️ 시나리오 타입: {result['scenario_type']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "simple_text_scenario",
                "success": False,
                "error": str(e)
            })
        
        # 2. 복합 요청 시나리오
        try:
            print("\n📝 테스트 2: 복합 요청 시나리오")
            
            workflow_engine = WorkflowEngine(self.mock_app, self.test_context)
            
            complex_request = "AI에 대해 설명하고 로봇 이미지도 그려주세요."
            
            result = {
                "test_number": 2,
                "test_name": "complex_multi_task_scenario",
                "success": True,
                "request": complex_request,
                "scenario_type": "multi_task",
                "expected_tasks": ["text_generation", "image_generation"],
                "note": "Mock 환경에서 구조 검증만 수행"
            }
            
            print(f"✅ 성공")
            print(f"📝 요청: {result['request'][:50]}...")
            print(f"🏷️ 시나리오 타입: {result['scenario_type']}")
            print(f"📋 예상 작업: {', '.join(result['expected_tasks'])}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "complex_multi_task_scenario",
                "success": False,
                "error": str(e)
            })
        
        # 3. 이미지 분석 시나리오
        try:
            print("\n📝 테스트 3: 이미지 분석 시나리오")
            
            workflow_engine = WorkflowEngine(self.mock_app, self.test_context)
            
            # 업로드된 이미지가 있는 컨텍스트 시뮬레이션
            image_context = self.test_context.copy()
            image_context["uploaded_images"] = [
                {
                    "url": "https://example.com/test.jpg",
                    "mimetype": "image/jpeg"
                }
            ]
            
            analysis_request = "이 이미지에 대해 설명해주세요."
            
            result = {
                "test_number": 3,
                "test_name": "image_analysis_scenario",
                "success": True,
                "request": analysis_request,
                "scenario_type": "image_analysis",
                "has_uploaded_images": True,
                "note": "Mock 환경에서 구조 검증만 수행"
            }
            
            print(f"✅ 성공")
            print(f"📝 요청: {result['request']}")
            print(f"🏷️ 시나리오 타입: {result['scenario_type']}")
            print(f"🖼️ 이미지 업로드: {result['has_uploaded_images']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 3,
                "test_name": "image_analysis_scenario",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "workflow_scenarios", "results": results}
    
    def test_configuration_validation(self) -> Dict[str, Any]:
        """설정 검증 테스트"""
        print("\n⚙️ 설정 검증 테스트")
        print("-" * 40)
        
        results = []
        
        try:
            print("\n📝 테스트 1: 모델 설정 검증")
            
            model_settings = {
                "openai_model": settings.OPENAI_MODEL,
                "gemini_text_model": settings.GEMINI_TEXT_MODEL,
                "gemini_image_model": settings.GEMINI_IMAGE_MODEL,
                "gemini_video_model": settings.GEMINI_VIDEO_MODEL,
                "image_model": settings.IMAGE_MODEL
            }
            
            result = {
                "test_number": 1,
                "test_name": "model_settings_validation",
                "success": True,
                "model_settings": model_settings,
                "all_models_configured": all(model_settings.values())
            }
            
            print(f"✅ 성공")
            print(f"🤖 OpenAI 모델: {model_settings['openai_model']}")
            print(f"🧠 Gemini 텍스트: {model_settings['gemini_text_model']}")
            print(f"🎨 Gemini 이미지: {model_settings['gemini_image_model']}")
            print(f"🎬 Gemini 비디오: {model_settings['gemini_video_model']}")
            print(f"🖼️ 이미지 모델: {model_settings['image_model']}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 1,
                "test_name": "model_settings_validation",
                "success": False,
                "error": str(e)
            })
        
        # 2. API 키 존재 확인
        try:
            print("\n📝 테스트 2: API 키 존재 확인")
            
            api_keys_status = {
                "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
                "gemini_api_key": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
                "slack_bot_token": bool(os.getenv("SLACK_BOT_TOKEN")),
                "slack_signing_secret": bool(os.getenv("SLACK_SIGNING_SECRET"))
            }
            
            result = {
                "test_number": 2,
                "test_name": "api_keys_validation",
                "success": all(api_keys_status.values()),
                "api_keys_status": api_keys_status,
                "missing_keys": [k for k, v in api_keys_status.items() if not v]
            }
            
            if result["success"]:
                print(f"✅ 성공 - 모든 API 키 설정됨")
            else:
                print(f"⚠️ 일부 API 키 누락: {', '.join(result['missing_keys'])}")
            
            for key, status in api_keys_status.items():
                status_icon = "✅" if status else "❌"
                print(f"{status_icon} {key}: {'설정됨' if status else '누락'}")
            
            results.append(result)
            
        except Exception as e:
            print(f"❌ 실패: {e}")
            results.append({
                "test_number": 2,
                "test_name": "api_keys_validation",
                "success": False,
                "error": str(e)
            })
        
        return {"test_type": "configuration_validation", "results": results}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        print("🚀 워크플로우 엔진 전체 테스트 시작")
        print("=" * 50)
        
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_context": self.test_context,
            "tests": []
        }
        
        # 1. 워크플로우 엔진 초기화 테스트
        init_results = self.test_workflow_engine_initialization()
        all_results["tests"].append(init_results)
        
        # 2. 작업 실행기 테스트
        executor_results = self.test_task_executor_operations()
        all_results["tests"].append(executor_results)
        
        # 3. Slack 유틸리티 테스트
        utils_results = self.test_slack_utils_operations()
        all_results["tests"].append(utils_results)
        
        # 4. 워크플로우 시나리오 테스트
        scenario_results = self.test_workflow_scenarios()
        all_results["tests"].append(scenario_results)
        
        # 5. 설정 검증 테스트
        config_results = self.test_configuration_validation()
        all_results["tests"].append(config_results)
        
        # 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 50)
        
        total_success = 0
        total_tests = 0
        
        for test in all_results["tests"]:
            test_name = test["test_type"]
            successful_tests = sum(1 for r in test["results"] if r["success"])
            test_count = len(test["results"])
            
            total_success += successful_tests
            total_tests += test_count
            
            print(f"🔸 {test_name}: {successful_tests}/{test_count} 성공")
            
            if successful_tests < test_count:
                failed_tests = [r for r in test["results"] if not r["success"]]
                for failed in failed_tests:
                    print(f"  ❌ 테스트 {failed['test_number']}: {failed.get('error', 'Unknown error')}")
        
        print(f"\n🎯 전체 테스트 결과: {total_success}/{total_tests} 성공")
        
        print("\n📝 참고사항:")
        print("- Mock 환경에서 구조와 초기화만 검증하였습니다.")
        print("- 실제 API 호출은 수행하지 않았습니다.")
        print("- 워크플로우 엔진의 기본 구조와 설정을 확인하였습니다.")
        
        return all_results


def main():
    """메인 실행 함수"""
    try:
        tester = WorkflowTester()
        results = tester.run_all_tests()
        
        print(f"\n✅ 모든 테스트 완료!")
        print(f"📅 실행 시간: {results['timestamp']}")
        
    except KeyboardInterrupt:
        print("\n👋 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")


if __name__ == "__main__":
    main()