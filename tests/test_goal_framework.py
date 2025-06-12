"""
Test Suite for Kor'tana's Goal Framework
Validates autonomous goal creation, management, and execution capabilities.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock

from kortana.core.goal_framework import Goal, GoalType, GoalStatus
from kortana.core.goal_manager import GoalManager


class TestGoal:
    """Test the core Goal data structure"""
    
    def test_goal_creation_defaults(self):
        """Test goal creation with default values"""
        goal = Goal()
        
        assert goal.goal_id.startswith("goal_")
        assert goal.type == GoalType.MAINTENANCE
        assert goal.status == GoalStatus.NEW
        assert goal.priority == 5
        assert goal.completion_percentage == 0.0
        assert not goal.covenant_approved
        assert goal.created_by == "autonomous"
    
    def test_goal_creation_with_parameters(self):
        """Test goal creation with specific parameters"""
        target_date = datetime.now(timezone.utc) + timedelta(days=7)
        
        goal = Goal(
            type=GoalType.LEARNING,
            title="Test Learning Goal",
            description="Learn something new",
            priority=8,
            target_completion=target_date,
            success_criteria=["Criterion 1", "Criterion 2"],
            required_capabilities=["capability_1", "capability_2"],
            estimated_effort="high"
        )
        
        assert goal.type == GoalType.LEARNING
        assert goal.title == "Test Learning Goal"
        assert goal.description == "Learn something new"
        assert goal.priority == 8
        assert goal.target_completion == target_date
        assert goal.success_criteria == ["Criterion 1", "Criterion 2"]
        assert goal.required_capabilities == ["capability_1", "capability_2"]
        assert goal.estimated_effort == "high"
    
    def test_goal_post_init(self):
        """Test goal post-initialization behavior"""
        goal = Goal(type=GoalType.IMPROVEMENT)
        
        # Should auto-generate title if not provided
        assert "Improvement Goal" in goal.title
        assert goal.goal_id[-8:] in goal.title
        
        # Should auto-generate description if not provided
        assert "Autonomous improvement goal" in goal.description
    
    def test_goal_to_dict(self):
        """Test goal serialization to dictionary"""
        goal = Goal(
            type=GoalType.USER_SERVICE,
            title="Test Goal",
            description="Test Description",
            priority=7
        )
        
        goal_dict = goal.to_dict()
        
        assert goal_dict["goal_id"] == goal.goal_id
        assert goal_dict["type"] == "user_service"
        assert goal_dict["title"] == "Test Goal"
        assert goal_dict["description"] == "Test Description"
        assert goal_dict["priority"] == 7
        assert goal_dict["status"] == "new"
        assert goal_dict["covenant_approved"] == False
    
    def test_goal_from_dict(self):
        """Test goal deserialization from dictionary"""
        goal_data = {
            "goal_id": "test_goal_123",
            "type": "learning",
            "title": "Test Learning",
            "description": "Test Description",
            "priority": 6,
            "status": "active",
            "success_criteria": ["Test criterion"],
            "covenant_approved": True
        }
        
        goal = Goal.from_dict(goal_data)
        
        assert goal.goal_id == "test_goal_123"
        assert goal.type == GoalType.LEARNING
        assert goal.title == "Test Learning"
        assert goal.description == "Test Description"
        assert goal.priority == 6
        assert goal.status == GoalStatus.ACTIVE
        assert goal.success_criteria == ["Test criterion"]
        assert goal.covenant_approved == True
    
    def test_goal_actionability(self):
        """Test goal actionability checks"""
        goal = Goal(
            type=GoalType.MAINTENANCE,
            status=GoalStatus.ACTIVE,
            priority=5,
            success_criteria=["Test criterion"],
            covenant_approved=True
        )
        
        assert goal.is_actionable()
        
        # Test low priority exclusion
        goal.priority = 2
        assert not goal.is_actionable()
        
        # Test covenant requirement
        goal.priority = 5
        goal.covenant_approved = False
        assert not goal.is_actionable()
        
        # Test success criteria requirement
        goal.covenant_approved = True
        goal.success_criteria = []
        assert not goal.is_actionable()
    
    def test_goal_activation(self):
        """Test goal activation"""
        goal = Goal(
            status=GoalStatus.NEW,
            success_criteria=["Test criterion"],
            covenant_approved=True
        )
        
        assert goal.can_be_activated()
        assert goal.activate()
        assert goal.status == GoalStatus.ACTIVE
        assert goal.started_at is not None
        
        # Cannot activate again
        assert not goal.activate()
    
    def test_goal_progress_update(self):
        """Test goal progress tracking"""
        goal = Goal(status=GoalStatus.ACTIVE)
        
        goal.update_progress(50.0, {"metric1": "value1"}, ["insight1"])
        
        assert goal.completion_percentage == 50.0
        assert goal.progress_metrics["metric1"] == "value1"
        assert "insight1" in goal.learning_insights
        
        # Test auto-completion at 100%
        goal.update_progress(100.0)
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completed_at is not None
    
    def test_goal_completion(self):
        """Test goal completion"""
        goal = Goal(status=GoalStatus.ACTIVE)
        
        lessons = {"lesson1": "value1", "lesson2": "value2"}
        goal.complete(lessons)
        
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completion_percentage == 100.0
        assert goal.completed_at is not None
        assert goal.lessons_learned == lessons
    
    def test_goal_pause_and_cancel(self):
        """Test goal pausing and cancellation"""
        goal = Goal(status=GoalStatus.ACTIVE)
        
        # Test pausing
        goal.pause("Test reason")
        assert goal.status == GoalStatus.PAUSED
        assert goal.context["pause_reason"] == "Test reason"
        
        # Test cancellation
        goal.cancel("Test cancellation")
        assert goal.status == GoalStatus.CANCELLED
        assert goal.context["cancellation_reason"] == "Test cancellation"
    
    def test_goal_time_calculations(self):
        """Test goal time-related calculations"""
        now = datetime.now(timezone.utc)
        future_date = now + timedelta(days=5)
        past_date = now - timedelta(days=2)
        
        # Test age calculation
        goal = Goal()
        goal.created_at = now - timedelta(days=3)
        assert abs(goal.get_age_days() - 3) < 0.1
        
        # Test time to deadline
        goal.target_completion = future_date
        time_left = goal.get_time_to_deadline_days()
        assert time_left is not None
        assert abs(time_left - 5) < 0.1
        
        # Test overdue detection
        goal.target_completion = past_date
        goal.status = GoalStatus.ACTIVE
        assert goal.is_overdue()
        
        goal.status = GoalStatus.COMPLETED
        assert not goal.is_overdue()


class TestGoalManager:
    """Test the GoalManager class"""
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Create mock memory manager"""
        memory_manager = Mock()
        memory_manager.store_memory = Mock()
        return memory_manager
    
    @pytest.fixture
    def mock_covenant_enforcer(self):
        """Create mock covenant enforcer"""
        covenant_enforcer = Mock()
        covenant_enforcer.verify_action = Mock(return_value=True)
        return covenant_enforcer
    
    @pytest.fixture
    def goal_manager(self, mock_memory_manager, mock_covenant_enforcer):
        """Create goal manager with mocks"""
        return GoalManager(
            memory_manager=mock_memory_manager,
            covenant_enforcer=mock_covenant_enforcer
        )
    
    def test_goal_manager_initialization(self, goal_manager):
        """Test goal manager initialization"""
        assert goal_manager.memory_manager is not None
        assert goal_manager.covenant_enforcer is not None
        assert len(goal_manager._goal_cache) == 0
        assert GoalType.MAINTENANCE in goal_manager._goal_templates
    
    def test_create_goal(self, goal_manager):
        """Test goal creation through manager"""
        goal = goal_manager.create_goal(
            goal_type=GoalType.LEARNING,
            title="Test Goal",
            description="Test Description",
            priority=7,
            success_criteria=["Success criterion"],
            required_capabilities=["capability1"]
        )
        
        assert goal.type == GoalType.LEARNING
        assert goal.title == "Test Goal"
        assert goal.description == "Test Description"
        assert goal.priority == 7
        assert goal.success_criteria == ["Success criterion"]
        assert goal.required_capabilities == ["capability1"]
        
        # Should be in cache
        assert goal.goal_id in goal_manager._goal_cache
        
        # Should call memory manager
        goal_manager.memory_manager.store_memory.assert_called()
    
    def test_create_goal_from_template(self, goal_manager):
        """Test goal creation from template"""
        goal = goal_manager.create_goal_from_template(
            GoalType.MAINTENANCE, 
            "code_health",
            priority=9  # Override default priority
        )
        
        assert goal is not None
        assert goal.type == GoalType.MAINTENANCE
        assert goal.title == "Maintain Code Health"
        assert goal.priority == 9  # Should use override
        assert "All linting checks pass" in goal.success_criteria
    
    def test_goal_retrieval(self, goal_manager):
        """Test goal retrieval by ID"""
        goal = goal_manager.create_goal(
            goal_type=GoalType.IMPROVEMENT,
            title="Test Retrieval Goal"
        )
        
        retrieved_goal = goal_manager.get_goal(goal.goal_id)
        assert retrieved_goal is not None
        assert retrieved_goal.goal_id == goal.goal_id
        assert retrieved_goal.title == "Test Retrieval Goal"
        
        # Test non-existent goal
        assert goal_manager.get_goal("non_existent_id") is None
    
    def test_goals_by_status(self, goal_manager):
        """Test filtering goals by status"""
        # Create goals with different statuses
        goal1 = goal_manager.create_goal(GoalType.MAINTENANCE, title="Goal 1")
        goal2 = goal_manager.create_goal(GoalType.LEARNING, title="Goal 2")
        goal2.status = GoalStatus.ACTIVE
        goal_manager._goal_cache[goal2.goal_id] = goal2  # Update cache
        
        new_goals = goal_manager.get_goals_by_status(GoalStatus.NEW)
        active_goals = goal_manager.get_goals_by_status(GoalStatus.ACTIVE)
        
        assert len(new_goals) == 1
        assert new_goals[0].goal_id == goal1.goal_id
        assert len(active_goals) == 1
        assert active_goals[0].goal_id == goal2.goal_id
    
    def test_goal_prioritization(self, goal_manager):
        """Test goal prioritization algorithm"""
        # Create goals with different priorities and types
        goal1 = goal_manager.create_goal(GoalType.MAINTENANCE, priority=5)
        goal2 = goal_manager.create_goal(GoalType.USER_SERVICE, priority=5)  # Should get type bonus
        goal3 = goal_manager.create_goal(GoalType.EXPLORATION, priority=7)  # High base but exploration penalty
        
        # Set deadline for urgency testing
        goal1.target_completion = datetime.now(timezone.utc) + timedelta(hours=12)  # Urgent
        
        prioritized = goal_manager.prioritize_goals()
        
        # Should be sorted by dynamic priority
        assert len(prioritized) == 3
        
        # Check that dynamic priorities were calculated
        for goal in prioritized:
            assert "dynamic_priority" in goal.context
    
    def test_goal_activation(self, goal_manager):
        """Test goal activation through manager"""
        goal = goal_manager.create_goal(
            GoalType.MAINTENANCE,
            success_criteria=["Test criterion"]
        )
        
        # Should activate successfully (covenant mock returns True)
        assert goal_manager.activate_goal(goal.goal_id)
        assert goal.status == GoalStatus.ACTIVE
        assert goal.covenant_approved
        
        # Test non-existent goal
        assert not goal_manager.activate_goal("non_existent_id")
    
    def test_goal_progress_update(self, goal_manager):
        """Test goal progress update through manager"""
        goal = goal_manager.create_goal(GoalType.IMPROVEMENT)
        
        success = goal_manager.update_goal_progress(
            goal.goal_id,
            75.0,
            {"test_metric": "value"},
            ["test insight"]
        )
        
        assert success
        assert goal.completion_percentage == 75.0
        assert goal.progress_metrics["test_metric"] == "value"
        assert "test insight" in goal.learning_insights
    
    def test_goal_completion(self, goal_manager):
        """Test goal completion through manager"""
        goal = goal_manager.create_goal(GoalType.LEARNING)
        
        lessons = {"lesson1": "Learned something important"}
        success = goal_manager.complete_goal(goal.goal_id, lessons)
        
        assert success
        assert goal.status == GoalStatus.COMPLETED
        assert goal.completion_percentage == 100.0
        assert goal.lessons_learned == lessons
    
    def test_autonomous_goal_suggestions(self, goal_manager):
        """Test autonomous goal suggestion generation"""
        # Test with no active maintenance goals
        suggestions = goal_manager.suggest_new_goals()
        
        # Should suggest at least maintenance and learning goals
        assert len(suggestions) >= 2
        
        goal_types = [g.type for g in suggestions]
        assert GoalType.MAINTENANCE in goal_types
        assert GoalType.LEARNING in goal_types
        
        # Test context-based suggestions
        context = {
            "performance_issues": True,
            "user_requests": True
        }
        
        context_suggestions = goal_manager.suggest_new_goals(context)
        
        # Should include improvement and user service goals
        context_types = [g.type for g in context_suggestions]
        assert GoalType.IMPROVEMENT in context_types
        assert GoalType.USER_SERVICE in context_types
    
    def test_covenant_enforcement(self, goal_manager):
        """Test Sacred Covenant integration"""
        # Test covenant approval
        goal = Goal(title="Test Goal", description="Test Description")
        
        approved = goal_manager._check_covenant_approval(goal)
        assert approved  # Mock returns True
        assert goal.covenant_approved
        assert "Approved by Sacred Covenant" in goal.covenant_review_notes
        
        # Test covenant rejection
        goal_manager.covenant_enforcer.verify_action.return_value = False
        goal2 = Goal(title="Blocked Goal")
        
        approved = goal_manager._check_covenant_approval(goal2)
        assert not approved
        assert not goal2.covenant_approved
        assert "Blocked by Sacred Covenant" in goal2.covenant_review_notes
    
    def test_statistics_generation(self, goal_manager):
        """Test goal statistics generation"""
        # Create goals with different statuses and types
        goal1 = goal_manager.create_goal(GoalType.MAINTENANCE, priority=5)
        goal2 = goal_manager.create_goal(GoalType.LEARNING, priority=7)
        goal2.complete()
        goal_manager._goal_cache[goal2.goal_id] = goal2
        
        stats = goal_manager.get_statistics()
        
        assert stats["total_goals"] == 2
        assert stats["by_status"]["new"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_type"]["maintenance"] == 1
        assert stats["by_type"]["learning"] == 1
        assert stats["completion_rate"] == 1.0  # 1 completed out of 1 finished
        assert stats["average_priority"] == 6.0  # (5 + 7) / 2


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main([__file__, "-v"])
