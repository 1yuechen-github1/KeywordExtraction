from fastapi import FastAPI, File, HTTPException, UploadFile

from kw_extract import kw_extract
from logger_config import logger
from dto.ImplantSurgeryRecordDto import ImplantSurgeryRecordDto

app = FastAPI()

logger.info("FastAPI 服务加载完成")


@app.get("/")
def read_root():
    return {
        "code": 0,
        "msg": "关键词提取服务运行正常",
    }

def get_category_value(grouped, category):
    """
    从“按类别”结果中取值。
    同一类别有多个关键词时，用中文逗号拼接。
    """
    return "，".join(grouped.get(category, []))


def result_to_implant_record(result):
    """
    将 kw_extract() 的结果转换为 ImplantSurgeryRecordDto。
    """
    grouped = result.get("按类别", {})

    # implant_brand = get_category_value(
    #     grouped,
    #     "治疗-种植体-品牌",
    # )

    # implant_model = get_category_value(
    #     grouped,
    #     "治疗-种植体-型号",
    # )

    # implant_diameter = get_category_value(
    #     grouped,
    #     "治疗-种植体-尺寸-直径",
    # )

    # implant_length = get_category_value(
    #     grouped,
    #     "治疗-种植体-尺寸-长度",
    # )

    # implant_type_parts = [
    #     part for part in (
    #         implant_brand,
    #         implant_model,
    #         implant_diameter,
    #         implant_length,
    #     )
    #     if part
    # ]

    implant_brand = get_category_value(
        grouped,
        "治疗-种植体-品牌",
    )

    implant_model = get_category_value(
        grouped,
        "治疗-种植体-型号",
    )

    implant_diameter = get_category_value(
        grouped,
        "治疗-种植体-尺寸-直径",
    )

    # implant_length = get_category_value(
    #     grouped,
    #     "治疗-种植体-尺寸-长度",
    # )



    # bone_grafting_parts = [
    #     part for part in (
    #         get_category_value(grouped, "治疗-植骨-骨粉品牌"),
    #         get_category_value(grouped, "治疗-植骨-克数"),
    #         get_category_value(grouped, "治疗-解剖-植骨位点-骨面"),
    #         get_category_value(grouped, "治疗-解剖-植骨位点-方向"),
    #     )
    #     if part
    # ]

    bone_graft_brand = get_category_value(
        grouped,
        "治疗-植骨-骨粉品牌",
    )

    bone_graft_amount = get_category_value(
        grouped,
        "治疗-植骨-克数",
    )

    bone_graft_surface = get_category_value(
        grouped,
        "治疗-解剖-植骨位点-骨面",
    )

    bone_graft_direction = get_category_value(
        grouped,
        "治疗-解剖-植骨位点-方向",
    )

    return ImplantSurgeryRecordDto(
        # 全身及局部情况
        systemicLocalCondition=get_category_value(
            grouped,
            "既往史-系统性疾病-阳性",
        ) or get_category_value(
            grouped,
            "既往史-系统性疾病-否认",
        ),

        # 手术信息
        surgeryName=get_category_value(
            grouped,
            "治疗-手术-术式",
        ),
        implantPosition=get_category_value(
            grouped,
            "专科检查-牙位-FDI编码",
        ),
        gingivalThickness=get_category_value(
            grouped,
            "专科检查-软组织-牙龈厚度",
        ),
        # implantType=" ".join(implant_type_parts),
        # boneGrafting="；".join(bone_grafting_parts),
        boneGraftBrand = bone_graft_brand,
        boneGraftAmount = bone_graft_amount,
        boneGraftSurface = bone_graft_surface,
        boneGraftDirection = bone_graft_direction,
        implantBrand = implant_brand,
        implantModel = implant_model,
        implantDiameter = implant_diameter,
        # implantlength = implant_length,
        barrierMembrane=get_category_value(
            grouped,
            "治疗-植骨-膜材料",
        ),
        implantTorque=get_category_value(
            grouped,
            "术后参数-种植体-扭力",
        ),
        transgingivalMethod=get_category_value(
            grouped,
            "术后参数-种植体-愈合方式",
        ),

        # 二期
        healingAbutmentType=get_category_value(
            grouped,
            "治疗-修复配件",
        ),

        # 修复
        abutmentInfo=get_category_value(
            grouped,
            "治疗-修复配件尺寸",
        ),
        prosthesisType=get_category_value(
            grouped,
            "治疗-修复-戴牙适配",
        ),

        # 备注：保留完整关键词结果，方便后续排查或人工确认
        surgeryNotes="；".join(
            f"{item['词']}（{item['类别']}）"
            for item in result.get("关键词", [])
        ),
    )


@app.post("/kw_extract")
async def kw_extract_api(file: UploadFile = File(...)):
    logger.info("收到文件上传请求，文件名=%s", file.filename)
    if not file.filename:
        logger.warning("上传失败：未选择文件")
        raise HTTPException(
            status_code=400,
            detail="未选择文件",
        )

    if not file.filename.lower().endswith(".txt"):
        logger.warning("上传失败：文件类型不支持，文件名=%s", file.filename)
        raise HTTPException(
            status_code=400,
            detail="只支持 TXT 文件",
        )

    try:
        file_bytes = await file.read()
        logger.info("文件读取完成，文件名=%s，字节数=%d", file.filename, len(file_bytes))

        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = file_bytes.decode("gbk")
            except UnicodeDecodeError:
                text = file_bytes.decode(
                    "utf-8",
                    errors="ignore",
                )



        result = kw_extract(text)
        implant_record = result_to_implant_record(result)
        logger.info("病例处理成功，文件名=%s，返回数据=%s", file.filename, implant_record.to_dict())
        # print("implant_record:",implant_record)
        return {
            "code": 0,
            "msg": "关键词提取成功",
            "data": implant_record.to_dict(),

            # 可选：保留原始抽取结果，便于 Java 侧调试
            # "extractResult": result,
        }


    except Exception as error:
        logger.exception("病例处理失败，文件名=%s，错误=%s", file.filename, error)
        raise HTTPException(
            status_code=500,
            detail=f"关键词提取失败：{error}",
        ) from error
