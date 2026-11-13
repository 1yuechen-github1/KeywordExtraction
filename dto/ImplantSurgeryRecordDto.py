from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Optional


# @dataclass
# class ImplantSurgeryRecordDto:
#     id: Optional[int] = None

#     # 全身及局部情况
#     systemicLocalCondition: Optional[str] = None

#     # 手术信息
#     surgeryTime: Optional[str] = None
#     surgeryName: Optional[str] = None
#     implantPosition: Optional[str] = None
#     boneQuality: Optional[str] = None
#     gingivalThickness: Optional[float] = None
#     implantType: Optional[str] = None
#     boneGrafting: Optional[str] = None
#     barrierMembrane: Optional[str] = None
#     implantTorque: Optional[str] = None
#     transgingivalMethod: Optional[str] = None
#     surgeryNotes: Optional[str] = None

#     # 导板信息
#     guideUsed: Optional[str] = None
#     guideCompany: Optional[str] = None
#     guideFitStatus: Optional[str] = None
#     poorFitReason: Optional[str] = None
#     guideProtocolChanged: Optional[str] = None
#     followupCtNeeded: Optional[str] = None
#     guideDesignType: Optional[str] = None
#     guideUsageType: Optional[str] = None
#     freehandMixed: Optional[str] = None
#     guideSpecialNotes: Optional[str] = None

#     # 二期手术信息
#     secondStageTime: Optional[str] = None
#     healingAbutmentType: Optional[str] = None

#     # 修复信息
#     restorationTime: Optional[datetime] = None
#     abutmentInfo: Optional[str] = None
#     prosthesisType: Optional[str] = None
#     afterDeliveryNotes: Optional[str] = None

#     # 复诊信息
#     followupTime: Optional[datetime] = None
#     followupStatus: Optional[str] = None

#     # 时间信息
#     createdAt: Optional[datetime] = None
#     updatedAt: Optional[datetime] = None

#     # 患者信息
#     patientname: Optional[str] = None
#     idcard: Optional[str] = None
#     sex: Optional[str] = None
#     birthday: Optional[str] = None
#     hospitalcode: Optional[str] = None
#     profession: Optional[str] = None
#     address: Optional[str] = None
#     incunabulum: Optional[str] = None
#     patientdoctor: Optional[str] = None
#     patientlabel: Optional[str] = None
#     patientlabelnote: Optional[str] = None

#     @classmethod
#     def from_dict(cls, data: dict[str, Any]):
#         """
#         根据字典创建对象。
#         支持 Java 的驼峰字段名和数据库下划线字段名。
#         """
#         snake_to_camel = {
#             "systemic_local_condition": "systemicLocalCondition",
#             "surgery_time": "surgeryTime",
#             "surgery_name": "surgeryName",
#             "implant_position": "implantPosition",
#             "bone_quality": "boneQuality",
#             "gingival_thickness": "gingivalThickness",
#             "implant_type": "implantType",
#             "bone_grafting": "boneGrafting",
#             "barrier_membrane": "barrierMembrane",
#             "implant_torque": "implantTorque",
#             "transgingival_method": "transgingivalMethod",
#             "surgery_notes": "surgeryNotes",
#             "guide_used": "guideUsed",
#             "guide_company": "guideCompany",
#             "guide_fit_status": "guideFitStatus",
#             "poor_fit_reason": "poorFitReason",
#             "guide_protocol_changed": "guideProtocolChanged",
#             "followup_ct_needed": "followupCtNeeded",
#             "guide_design_type": "guideDesignType",
#             "guide_usage_type": "guideUsageType",
#             "freehand_mixed": "freehandMixed",
#             "guide_special_notes": "guideSpecialNotes",
#             "second_stage_time": "secondStageTime",
#             "healing_abutment_type": "healingAbutmentType",
#             "restoration_time": "restorationTime",
#             "abutment_info": "abutmentInfo",
#             "prosthesis_type": "prosthesisType",
#             "after_delivery_notes": "afterDeliveryNotes",
#             "followup_time": "followupTime",
#             "followup_status": "followupStatus",
#             "created_at": "createdAt",
#             "updated_at": "updatedAt",
#             "patient_name": "patientname",
#             "id_card": "idcard",
#             "hospital_code": "hospitalcode",
#             "patient_doctor": "patientdoctor",
#             "patient_label": "patientlabel",
#             "patient_label_note": "patientlabelnote",
#         }

#         normalized_data = {}

#         valid_fields = {
#             field.name
#             for field in fields(cls)
#         }

#         for key, value in data.items():
#             target_key = snake_to_camel.get(key, key)

#             if target_key in valid_fields:
#                 normalized_data[target_key] = value

#         return cls(**normalized_data)

#     def to_dict(self) -> dict[str, Any]:
#         """
#         转换为字典，字段名保持 Java DTO 的驼峰格式。
#         """
#         return {
#             field.name: getattr(self, field.name)
#             for field in fields(self)
#         }

@dataclass
class ImplantSurgeryRecordDto:
    id: Optional[int] = None

    # 全身及局部情况
    systemicLocalCondition: Optional[str] = None

    # 手术信息
    surgeryTime: Optional[str] = None
    surgeryName: Optional[str] = None
    implantPosition: Optional[str] = None
    boneQuality: Optional[str] = None
    gingivalThickness: Optional[float] = None

    # 种植体信息：拆分保存
    implantBrand: Optional[str] = None
    implantModel: Optional[str] = None
    implantDiameter: Optional[str] = None
    implantLength: Optional[str] = None

    # 如果数据库暂时还保留这个字段，可以保留；
    # 不再把四项内容拼接到这里
    implantType: Optional[str] = None

    boneGrafting: Optional[str] = None
    barrierMembrane: Optional[str] = None
    implantTorque: Optional[str] = None
    transgingivalMethod: Optional[str] = None
    surgeryNotes: Optional[str] = None

    # 导板信息
    guideUsed: Optional[str] = None
    guideCompany: Optional[str] = None
    guideFitStatus: Optional[str] = None
    poorFitReason: Optional[str] = None
    guideProtocolChanged: Optional[str] = None
    followupCtNeeded: Optional[str] = None
    guideDesignType: Optional[str] = None
    guideUsageType: Optional[str] = None
    freehandMixed: Optional[str] = None
    guideSpecialNotes: Optional[str] = None

    # 二期手术信息
    secondStageTime: Optional[str] = None
    healingAbutmentType: Optional[str] = None

    # 修复信息
    restorationTime: Optional[datetime] = None
    abutmentInfo: Optional[str] = None
    prosthesisType: Optional[str] = None
    afterDeliveryNotes: Optional[str] = None

    # 复诊信息
    followupTime: Optional[datetime] = None
    followupStatus: Optional[str] = None

    # 时间信息
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    # 植骨信息：拆分保存
    boneGraftBrand: Optional[str] = None
    boneGraftAmount: Optional[str] = None
    boneGraftSurface: Optional[str] = None
    boneGraftDirection: Optional[str] = None


    # 患者信息
    patientname: Optional[str] = None
    idcard: Optional[str] = None
    sex: Optional[str] = None
    birthday: Optional[str] = None
    hospitalcode: Optional[str] = None
    profession: Optional[str] = None
    address: Optional[str] = None
    incunabulum: Optional[str] = None
    patientdoctor: Optional[str] = None
    patientlabel: Optional[str] = None
    patientlabelnote: Optional[str] = None


    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        """
        根据字典创建对象。
        支持 Java 的驼峰字段名和数据库下划线字段名。
        """
        snake_to_camel = {
            "systemic_local_condition": "systemicLocalCondition",
            "surgery_time": "surgeryTime",
            "surgery_name": "surgeryName",
            "implant_position": "implantPosition",
            "implant_brand": "implantBrand",
            "implant_model": "implantModel",
            "implant_diameter": "implantDiameter",
            "implant_length": "implantLength",
            "bone_quality": "boneQuality",
            "gingival_thickness": "gingivalThickness",
            "implant_type": "implantType",
            # "bone_grafting": "boneGrafting",
            
            "bone_graft_brand":"boneGraftBrand",
            "bone_graft_amount":"boneGraftAmount",
            "bone_graft_surface":"boneGraftSurface",
            "bone_graftdirection":"boneGraftDirection",

            "barrier_membrane": "barrierMembrane",
            "implant_torque": "implantTorque",
            "transgingival_method": "transgingivalMethod",
            "surgery_notes": "surgeryNotes",
            "guide_used": "guideUsed",
            "guide_company": "guideCompany",
            "guide_fit_status": "guideFitStatus",
            "poor_fit_reason": "poorFitReason",
            "guide_protocol_changed": "guideProtocolChanged",
            "followup_ct_needed": "followupCtNeeded",
            "guide_design_type": "guideDesignType",
            "guide_usage_type": "guideUsageType",
            "freehand_mixed": "freehandMixed",
            "guide_special_notes": "guideSpecialNotes",
            "second_stage_time": "secondStageTime",
            "healing_abutment_type": "healingAbutmentType",
            "restoration_time": "restorationTime",
            "abutment_info": "abutmentInfo",
            "prosthesis_type": "prosthesisType",
            "after_delivery_notes": "afterDeliveryNotes",
            "followup_time": "followupTime",
            "followup_status": "followupStatus",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "patient_name": "patientname",
            "id_card": "idcard",
            "hospital_code": "hospitalcode",
            "patient_doctor": "patientdoctor",
            "patient_label": "patientlabel",
            "patient_label_note": "patientlabelnote",
        }

        normalized_data = {}

        valid_fields = {
            field.name
            for field in fields(cls)
        }

        for key, value in data.items():
            target_key = snake_to_camel.get(key, key)

            if target_key in valid_fields:
                normalized_data[target_key] = value

        return cls(**normalized_data)

    def to_dict(self) -> dict[str, Any]:
        """
        转换为字典，字段名保持 Java DTO 的驼峰格式。
        """
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
        }