from abc import ABC
from typing import Any
from typing import Callable
from typing import cast

from django import forms
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.forms.widgets import MediaAsset


class SelfScript(MediaAsset):
    element_template = "<!-- {attributes} {path} -->"
    render_template = "<script {attributes}> {code} </script>"

    def __init__(self, script: str, **attributes: Any):
        self.attributes = attributes
        self.code = script
        super().__init__(script, **attributes)

    def __str__(self) -> str:
        return self.render_template.format_map(
            {"attributes": self.attributes, "code": self.code}
        )


class ComponentBaseForm(forms.ModelForm[Any]):
    components: list["FormComponentInterface"] = []
    __pre_save_hooks: list[Callable[["ComponentBaseForm"], Any]] = []
    __post_save_hooks: list[Callable[["ComponentBaseForm"], Any]] = []

    class Media:
        js = [
            SelfScript(
                """
document.addEventListener("DOMContentLoaded", function() {
    const inputs = document.querySelectorAll("input[has_datalist]");
    if (inputs.length <= 0) return;
    inputs.forEach((input) => {
        if (input) {
            let dataList = input.parentElement.querySelector('datalist');
            if (!dataList) {
                dataList = document.createElement("datalist");
                dataList.id = `${input.getAttribute("list")}`;
                input.after(dataList);
            }
            let choices = input.getAttribute("autocomplete");
            if (choices) {
                choices.split("\x07").forEach(function(choice) {
                    const option = document.createElement("option");
                    option.value = choice;
                    dataList.appendChild(option);
                });
            }
        }
    })
});"""
            )
        ]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)  # type:ignore
        for component in self.components:
            component.apply(self)

    def set_save_hook(
        self,
        hook: Callable[["ComponentBaseForm"], Any],
        is_pre_save: bool = True,
    ):
        if is_pre_save:
            self.__pre_save_hooks.append(hook)
        else:
            self.__post_save_hooks.append(hook)

    def full_clean(self) -> None:
        for save_hook in self.__pre_save_hooks:
            save_hook(self)

        return super().full_clean()

    def save(self, commit: bool = True):
        res = cast(bool, super().save(commit))
        for save_hook in self.__post_save_hooks:
            save_hook(self)
        return res


class FormComponentInterface(ABC):
    def apply(self, on_class: ComponentBaseForm):
        pass


class DataListFormComponent(FormComponentInterface):
    def __init__(self, model_field_tuple: list[tuple[Any, str]] = []):
        self.model_field_tuple = model_field_tuple

    def apply(self, on_class: forms.ModelForm[Any]):
        for model, field in self.model_field_tuple:
            existing_body_types = model.objects.values_list("name", flat=True)
            on_class.fields[field].widget = forms.TextInput()
            on_class.fields[field].widget.attrs.update(
                {
                    "list": f"{field}_list",
                    "autocomplete": "\a".join(
                        [i for i in existing_body_types]
                    ),
                    "has_datalist": True,
                }
            )


class ImageUploadFormComponent(FormComponentInterface):
    uploaded_tracker: list[str] = []

    def __init__(self, picture_fields: list[str] = []):
        self.picture_fields = picture_fields

    def upload_and_save(self, on_class: ComponentBaseForm, field: str):
        upload = on_class.files.get(field)
        if upload:
            self.uploaded_tracker.append(field)
            path = default_storage.save(
                f"profile_pictures/{upload.name}", ContentFile(upload.read())
            )

            file_url = default_storage.url(path)
            on_class.instance.__setattr__(field, file_url)  # type:ignore
            on_class.fields.pop(field)

    def save(self, on_class: ComponentBaseForm):
        for field in self.picture_fields:
            if field and field not in self.uploaded_tracker:
                self.upload_and_save(on_class, field)

    def apply(self, on_class: ComponentBaseForm):
        on_class.set_save_hook(self.save, is_pre_save=True)
        for field_name in self.picture_fields:
            on_class.fields[field_name] = forms.ImageField(
                required=False, help_text="Upload a profile picture"
            )
