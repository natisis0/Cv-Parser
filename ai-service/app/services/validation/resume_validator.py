import re


class ResumeValidator:

    def validate(self, resume):
        errors = []

        # EMAIL
        if not resume.personal_info or not resume.personal_info.email:
            errors.append("Missing email")

        # NAME
        if not resume.personal_info or not resume.personal_info.full_name:
            errors.append("Missing name")

        # EXPERIENCE
        if not resume.experience:
            errors.append("No experience found")

        # EMAIL FORMAT CHECK
        if resume.personal_info and resume.personal_info.email:
            if not re.match(r".+@.+\..+", resume.personal_info.email):
                errors.append("Invalid email format")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
