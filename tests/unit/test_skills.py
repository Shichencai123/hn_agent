"""技能系统单元测试。"""

from __future__ import annotations

import os
import textwrap

import pytest

from hn_agent.exceptions import SkillValidationError
from hn_agent.skills import (
    Skill,
    SkillInstaller,
    SkillLoader,
    SkillParser,
    validate_frontmatter,
    validate_skill_content,
)


# ── Skill 数据模型测试 ───────────────────────────────────


class TestSkill:
    def test_defaults(self):
        skill = Skill(name="test", description="desc")
        assert skill.name == "test"
        assert skill.description == "desc"
        assert skill.dependencies == []
        assert skill.prompt == ""

    def test_full_construction(self):
        skill = Skill(
            name="code-review",
            description="代码审查技能",
            dependencies=["bash", "read"],
            prompt="你是一个代码审查专家。",
        )
        assert skill.name == "code-review"
        assert skill.dependencies == ["bash", "read"]
        assert skill.prompt == "你是一个代码审查专家。"


# ── 验证函数测试 ─────────────────────────────────────────


class TestValidateFrontmatter:
    def test_valid_frontmatter(self):
        # 不应抛出异常
        validate_frontmatter({"name": "test", "description": "desc"})

    def test_missing_name(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({"description": "desc"})
        assert any(e["field"] == "name" for e in exc_info.value.errors)

    def test_missing_description(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({"name": "test"})
        assert any(e["field"] == "description" for e in exc_info.value.errors)

    def test_missing_both(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({})
        assert len(exc_info.value.errors) == 2

    def test_empty_name(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({"name": "", "description": "desc"})
        assert any(
            e["field"] == "name" and e["error"] == "empty"
            for e in exc_info.value.errors
        )

    def test_whitespace_only_name(self):
        with pytest.raises(SkillValidationError):
            validate_frontmatter({"name": "   ", "description": "desc"})

    def test_invalid_dependencies_type(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({
                "name": "test",
                "description": "desc",
                "dependencies": "not-a-list",
            })
        assert any(e["field"] == "dependencies" for e in exc_info.value.errors)

    def test_valid_dependencies(self):
        # 不应抛出异常
        validate_frontmatter({
            "name": "test",
            "description": "desc",
            "dependencies": ["bash", "read"],
        })

    def test_source_in_error(self):
        with pytest.raises(SkillValidationError) as exc_info:
            validate_frontmatter({}, source="skills/test/SKILL.md")
        assert any(
            e["source"] == "skills/test/SKILL.md"
            for e in exc_info.value.errors
        )


class TestValidateSkillContent:
    def test_empty_content(self):
        with pytest.raises(SkillValidationError, match="内容为空"):
            validate_skill_content("")

    def test_whitespace_only(self):
        with pytest.raises(SkillValidationError, match="内容为空"):
            validate_skill_content("   \n  ")

    def test_no_frontmatter(self):
        with pytest.raises(SkillValidationError, match="frontmatter"):
            validate_skill_content("# Just markdown")

    def test_unclosed_frontmatter(self):
        with pytest.raises(SkillValidationError, match="未闭合"):
            validate_skill_content("---\nname: test\n")

    def test_valid_content(self):
        content = "---\nname: test\ndescription: desc\n---\nBody"
        # 不应抛出异常
        validate_skill_content(content)


# ── SkillParser 测试 ─────────────────────────────────────


class TestSkillParser:
    @pytest.fixture()
    def parser(self) -> SkillParser:
        return SkillParser()

    def test_parse_minimal(self, parser: SkillParser):
        content = textwrap.dedent("""\
            ---
            name: test-skill
            description: A test skill
            ---
            This is the prompt.
        """)
        skill = parser.parse(content)
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.dependencies == []
        assert skill.prompt == "This is the prompt."

    def test_parse_with_dependencies(self, parser: SkillParser):
        content = textwrap.dedent("""\
            ---
            name: code-review
            description: 代码审查
            dependencies:
              - bash
              - read
            ---
            你是一个代码审查专家。
        """)
        skill = parser.parse(content)
        assert skill.name == "code-review"
        assert skill.dependencies == ["bash", "read"]

    def test_parse_multiline_prompt(self, parser: SkillParser):
        content = textwrap.dedent("""\
            ---
            name: writer
            description: Writing assistant
            ---
            # Writing Guide

            You are a writing assistant.

            ## Rules
            - Be concise
            - Be clear
        """)
        skill = parser.parse(content)
        assert "# Writing Guide" in skill.prompt
        assert "## Rules" in skill.prompt
        assert "- Be concise" in skill.prompt

    def test_parse_empty_body(self, parser: SkillParser):
        content = "---\nname: empty\ndescription: No body\n---\n"
        skill = parser.parse(content)
        assert skill.name == "empty"
        assert skill.prompt == ""

    def test_parse_invalid_yaml(self, parser: SkillParser):
        content = "---\n: invalid: yaml: [[\n---\nBody"
        with pytest.raises(SkillValidationError, match="YAML"):
            parser.parse(content)

    def test_parse_missing_required_field(self, parser: SkillParser):
        content = "---\nname: test\n---\nBody"
        with pytest.raises(SkillValidationError):
            parser.parse(content)

    def test_parse_no_frontmatter(self, parser: SkillParser):
        with pytest.raises(SkillValidationError):
            parser.parse("Just markdown content")

    def test_parse_empty_content(self, parser: SkillParser):
        with pytest.raises(SkillValidationError):
            parser.parse("")

    def test_parse_source_propagated(self, parser: SkillParser):
        """source 参数应传递到错误信息中。"""
        with pytest.raises(SkillValidationError) as exc_info:
            parser.parse("---\n---\nBody", source="my/SKILL.md")
        assert any(
            e.get("source") == "my/SKILL.md"
            for e in exc_info.value.errors
        )

    def test_parse_null_dependencies_treated_as_empty(self, parser: SkillParser):
        content = "---\nname: test\ndescription: desc\ndependencies:\n---\nBody"
        skill = parser.parse(content)
        assert skill.dependencies == []


# ── SkillLoader 测试 ─────────────────────────────────────


class TestSkillLoader:
    @pytest.fixture()
    def skills_dir(self, tmp_path):
        """创建包含多个技能的临时目录。"""
        # 技能 1: 子目录形式
        skill1_dir = tmp_path / "skill-a"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text(
            "---\nname: skill-a\ndescription: Skill A\n---\nPrompt A",
            encoding="utf-8",
        )

        # 技能 2: 子目录形式
        skill2_dir = tmp_path / "skill-b"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text(
            "---\nname: skill-b\ndescription: Skill B\ndependencies:\n  - bash\n---\nPrompt B",
            encoding="utf-8",
        )

        # 非技能目录（无 SKILL.md）
        (tmp_path / "not-a-skill").mkdir()

        return tmp_path

    def test_discover_finds_all_skills(self, skills_dir):
        loader = SkillLoader(str(skills_dir))
        skills = loader.discover()
        assert len(skills) == 2
        names = {s.name for s in skills}
        assert names == {"skill-a", "skill-b"}

    def test_discover_nonexistent_dir(self):
        loader = SkillLoader("/nonexistent/path")
        skills = loader.discover()
        assert skills == []

    def test_discover_empty_dir(self, tmp_path):
        loader = SkillLoader(str(tmp_path))
        skills = loader.discover()
        assert skills == []

    def test_discover_skips_invalid_files(self, tmp_path):
        """无效的 SKILL.md 应被跳过而非中断发现。"""
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "SKILL.md").write_text(
            "---\nname: valid\ndescription: Valid\n---\nOK",
            encoding="utf-8",
        )

        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()
        (invalid_dir / "SKILL.md").write_text("no frontmatter", encoding="utf-8")

        loader = SkillLoader(str(tmp_path))
        skills = loader.discover()
        assert len(skills) == 1
        assert skills[0].name == "valid"

    def test_load_from_cache(self, skills_dir):
        loader = SkillLoader(str(skills_dir))
        loader.discover()  # 填充缓存
        skill = loader.load("skill-a")
        assert skill.name == "skill-a"

    def test_load_from_directory(self, skills_dir):
        loader = SkillLoader(str(skills_dir))
        # 不调用 discover，直接按名称加载
        skill = loader.load("skill-a")
        assert skill.name == "skill-a"

    def test_load_nonexistent_skill(self, skills_dir):
        loader = SkillLoader(str(skills_dir))
        with pytest.raises(SkillValidationError, match="不存在"):
            loader.load("nonexistent")

    def test_discover_with_override_dir(self, skills_dir, tmp_path):
        """discover 可以传入不同的目录。"""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        (other_dir / "SKILL.md").write_text(
            "---\nname: other\ndescription: Other\n---\nOther prompt",
            encoding="utf-8",
        )

        loader = SkillLoader(str(skills_dir))
        skills = loader.discover(str(other_dir))
        # other_dir 下直接有 SKILL.md
        assert len(skills) == 1
        assert skills[0].name == "other"

    def test_skills_dir_property(self):
        loader = SkillLoader("/some/path")
        assert loader.skills_dir == "/some/path"


# ── SkillInstaller 测试 ──────────────────────────────────


class TestSkillInstaller:
    def test_install_raises_not_implemented(self):
        installer = SkillInstaller()
        with pytest.raises(NotImplementedError):
            installer.install("https://example.com/skill.tar.gz", "/tmp/skills")

    def test_constructor_accepts_loader(self):
        loader = SkillLoader()
        installer = SkillInstaller(loader=loader)
        assert installer._loader is loader


# ── __init__.py 导出测试 ─────────────────────────────────


class TestSkillsExports:
    def test_all_exports_importable(self):
        from hn_agent import skills

        assert hasattr(skills, "Skill")
        assert hasattr(skills, "SkillParser")
        assert hasattr(skills, "SkillLoader")
        assert hasattr(skills, "SkillInstaller")
        assert hasattr(skills, "validate_frontmatter")
        assert hasattr(skills, "validate_skill_content")
