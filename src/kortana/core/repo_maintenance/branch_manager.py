"""
Branch Manager Module

Manages git branches including cleanup and naming convention enforcement.
"""

import subprocess
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import re


@dataclass
class BranchInfo:
    """Information about a git branch."""
    name: str
    last_commit_date: datetime
    is_merged: bool
    is_active: bool
    follows_convention: bool
    age_days: int


class BranchManager:
    """Manages git branches with cleanup and optimization features."""
    
    # Standard branch naming conventions
    NAMING_CONVENTIONS = {
        "feature": r"^feature/[\w-]+$",
        "bugfix": r"^bugfix/[\w-]+$",
        "hotfix": r"^hotfix/[\w-]+$",
        "release": r"^release/[\w-]+$",
        "develop": r"^develop$",
        "main": r"^main$",
        "master": r"^master$",
    }
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.logger = logging.getLogger(__name__)
    
    def analyze_branches(self) -> List[BranchInfo]:
        """Analyze all branches in the repository."""
        branches = []
        
        try:
            # Get all branches
            result = subprocess.run(
                ["git", "branch", "-a", "--format=%(refname:short)"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            branch_names = [b.strip() for b in result.stdout.split('\n') if b.strip()]
            
            for branch_name in branch_names:
                if branch_name.startswith('origin/'):
                    continue  # Skip remote tracking branches for now
                
                branch_info = self._get_branch_info(branch_name)
                if branch_info:
                    branches.append(branch_info)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error analyzing branches: {e}")
        
        return branches
    
    def _get_branch_info(self, branch_name: str) -> Optional[BranchInfo]:
        """Get detailed information about a branch."""
        try:
            # Get last commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ct", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return None
            
            timestamp = int(result.stdout.strip())
            last_commit_date = datetime.fromtimestamp(timestamp)
            age_days = (datetime.now() - last_commit_date).days
            
            # Check if merged
            is_merged = self._is_branch_merged(branch_name)
            
            # Check naming convention
            follows_convention = self._check_naming_convention(branch_name)
            
            # Consider branch active if committed to in last 30 days
            is_active = age_days < 30
            
            return BranchInfo(
                name=branch_name,
                last_commit_date=last_commit_date,
                is_merged=is_merged,
                is_active=is_active,
                follows_convention=follows_convention,
                age_days=age_days
            )
        
        except Exception as e:
            self.logger.debug(f"Error getting info for branch {branch_name}: {e}")
            return None
    
    def _is_branch_merged(self, branch_name: str) -> bool:
        """Check if a branch has been merged."""
        try:
            result = subprocess.run(
                ["git", "branch", "--merged", "main"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            merged_branches = result.stdout.split('\n')
            return any(branch_name in branch for branch in merged_branches)
        
        except subprocess.CalledProcessError:
            # Try with master if main doesn't exist
            try:
                result = subprocess.run(
                    ["git", "branch", "--merged", "master"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                merged_branches = result.stdout.split('\n')
                return any(branch_name in branch for branch in merged_branches)
            except:
                return False
    
    def _check_naming_convention(self, branch_name: str) -> bool:
        """Check if branch follows naming conventions."""
        for convention_regex in self.NAMING_CONVENTIONS.values():
            if re.match(convention_regex, branch_name):
                return True
        return False
    
    def get_stale_branches(self, days_threshold: int = 90) -> List[BranchInfo]:
        """
        Get branches that haven't been updated in a while.
        
        Args:
            days_threshold: Number of days to consider a branch stale
        
        Returns:
            List of stale branches
        """
        branches = self.analyze_branches()
        return [
            branch for branch in branches
            if branch.age_days > days_threshold
            and branch.name not in ['main', 'master', 'develop']
        ]
    
    def get_non_compliant_branches(self) -> List[BranchInfo]:
        """Get branches that don't follow naming conventions."""
        branches = self.analyze_branches()
        return [
            branch for branch in branches
            if not branch.follows_convention
            and branch.name not in ['HEAD']
        ]
    
    def get_cleanup_recommendations(self) -> Dict[str, List[str]]:
        """Get recommendations for branch cleanup."""
        branches = self.analyze_branches()
        
        recommendations = {
            "merged_and_stale": [],
            "stale_but_not_merged": [],
            "non_compliant_naming": [],
            "safe_to_delete": []
        }
        
        for branch in branches:
            if branch.name in ['main', 'master', 'develop', 'HEAD']:
                continue
            
            if branch.is_merged and branch.age_days > 30:
                recommendations["merged_and_stale"].append(branch.name)
                recommendations["safe_to_delete"].append(branch.name)
            elif branch.age_days > 90:
                recommendations["stale_but_not_merged"].append(branch.name)
            
            if not branch.follows_convention:
                recommendations["non_compliant_naming"].append(branch.name)
        
        return recommendations
    
    def get_branch_report(self) -> Dict[str, Any]:
        """Generate a comprehensive branch report."""
        branches = self.analyze_branches()
        
        active_count = sum(1 for b in branches if b.is_active)
        merged_count = sum(1 for b in branches if b.is_merged)
        compliant_count = sum(1 for b in branches if b.follows_convention)
        
        return {
            "total_branches": len(branches),
            "active_branches": active_count,
            "merged_branches": merged_count,
            "compliant_branches": compliant_count,
            "compliance_rate": f"{(compliant_count/len(branches)*100):.1f}%" if branches else "N/A",
            "cleanup_candidates": len(self.get_stale_branches())
        }
