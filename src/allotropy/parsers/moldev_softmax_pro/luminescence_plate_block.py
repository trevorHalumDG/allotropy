from typing import Any
import uuid

from allotropy.allotrope.models.luminescence_benchling_2023_09_luminescence import (
    DeviceControlAggregateDocument,
    DeviceControlDocumentItem,
    MeasurementAggregateDocument,
    MeasurementDocumentItem,
    Model,
)
from allotropy.allotrope.models.shared.definitions.custom import (
    TQuantityValueDegreeCelsius,
    TQuantityValueNanometer,
    TQuantityValueNumber,
)
from allotropy.parsers.moldev_softmax_pro.fluorescence_plate_block import (
    FluorescenceOrLuminescencePlateBlock,
)
from allotropy.parsers.moldev_softmax_pro.plate_block import WellData
from allotropy.parsers.utils.values import natural_sort_key


class LuminescencePlateBlock(FluorescenceOrLuminescencePlateBlock):
    READ_MODE = "Luminescence"
    CONCEPT = "luminescence"
    UNIT = "RLU"
    DATA_TYPE_IDX = 6
    EXCITATION_WAVELENGTHS_IDX = 19

    def generate_device_control_doc(self) -> DeviceControlDocumentItem:
        device_control_doc = DeviceControlDocumentItem(
            detector_gain_setting=self.pmt_gain
        )

        if self.is_single_wavelength:
            device_control_doc.detector_wavelength_setting = TQuantityValueNanometer(
                self.wavelengths[0]
            )

        return device_control_doc

    def generate_measurement_doc(
        self, well: str, well_data: WellData
    ) -> MeasurementDocumentItem:
        measurement = MeasurementDocumentItem(
            DeviceControlAggregateDocument([self.generate_device_control_doc()]),
            self.generate_sample_document(well),
        )

        if well_data.temperature is not None:
            measurement.compartment_temperature = TQuantityValueDegreeCelsius(
                float(well_data.temperature)
            )

        if not well_data.is_empty:
            measurement.data_cube = self.generate_data_cube(well_data)

        if well_data.processed_data:
            measurement.processed_data_aggregate_document = (
                self.generate_processed_data_aggreate_document(well_data)
            )

        return measurement

    def to_allotrope(self) -> Any:
        wells = sorted(self.well_data.keys(), key=natural_sort_key)

        allotrope_file = Model(
            measurement_aggregate_document=MeasurementAggregateDocument(
                measurement_identifier=str(uuid.uuid4()),
                plate_well_count=TQuantityValueNumber(self.num_wells),
                measurement_document=[
                    self.generate_measurement_doc(well, self.well_data[well])
                    for well in wells
                ],
            )
        )

        return allotrope_file
