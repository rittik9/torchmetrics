# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections.abc import Sequence
from typing import Any, Optional, Union

from torch import Tensor

from torchmetrics.detection.iou import IntersectionOverUnion
from torchmetrics.functional.detection.giou import _giou_compute, _giou_update
from torchmetrics.utilities.imports import _MATPLOTLIB_AVAILABLE, _TORCHVISION_AVAILABLE
from torchmetrics.utilities.plot import _AX_TYPE, _PLOT_OUT_TYPE

if not _TORCHVISION_AVAILABLE:
    __doctest_skip__ = ["GeneralizedIntersectionOverUnion", "GeneralizedIntersectionOverUnion.plot"]
elif not _MATPLOTLIB_AVAILABLE:
    __doctest_skip__ = ["GeneralizedIntersectionOverUnion.plot"]


class GeneralizedIntersectionOverUnion(IntersectionOverUnion):
    r"""Compute Generalized Intersection Over Union (`GIoU`_).

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~List`): A list consisting of dictionaries each containing the key-values
      (each dictionary corresponds to a single image). Parameters that should be provided per dict:

        - ``boxes`` (:class:`~torch.Tensor`): float tensor of shape ``(num_boxes, 4)`` containing ``num_boxes``
          detection boxes of the format specified in the constructor.
          By default, this method expects ``(xmin, ymin, xmax, ymax)`` in absolute image coordinates.
        - ``labels`` (:class:`~torch.Tensor`): integer tensor of shape ``(num_boxes)`` containing 0-indexed detection
          classes for the boxes.

    - ``target`` (:class:`~List`): A list consisting of dictionaries each containing the key-values
      (each dictionary corresponds to a single image). Parameters that should be provided per dict:

        - ``boxes`` (:class:`~torch.Tensor`): float tensor of shape ``(num_boxes, 4)`` containing ``num_boxes`` ground
          truth boxes of the format specified in the constructor.
          By default, this method expects ``(xmin, ymin, xmax, ymax)`` in absolute image coordinates.
        - ``labels`` (:class:`~torch.Tensor`): integer tensor of shape ``(num_boxes)`` containing 0-indexed ground truth
          classes for the boxes.

    As output of ``forward`` and ``compute`` the metric returns the following output:

    - ``giou_dict``: A dictionary containing the following key-values:

        - giou: (:class:`~torch.Tensor`) with overall giou value over all classes and samples.
        - giou/cl_{cl}: (:class:`~torch.Tensor`), if argument ``class metrics=True``

    Args:
        box_format:
            Input format of given boxes. Supported formats are ``[`xyxy`, `xywh`, `cxcywh`]``.
        iou_thresholds:
            Optional IoU thresholds for evaluation. If set to `None` the threshold is ignored.
        class_metrics:
            Option to enable per-class metrics for IoU. Has a performance impact.
        respect_labels:
            Ignore values from boxes that do not have the same label as the ground truth box. Else will compute Iou
            between all pairs of boxes.
        kwargs:
            Additional keyword arguments, see :ref:`Metric kwargs` for more info.

    Example:
        >>> import torch
        >>> from torchmetrics.detection import GeneralizedIntersectionOverUnion
        >>> preds = [
        ...    {
        ...        "boxes": torch.tensor([[296.55, 93.96, 314.97, 152.79], [298.55, 98.96, 314.97, 151.79]]),
        ...        "scores": torch.tensor([0.236, 0.56]),
        ...        "labels": torch.tensor([4, 5]),
        ...    }
        ... ]
        >>> target = [
        ...    {
        ...        "boxes": torch.tensor([[300.00, 100.00, 315.00, 150.00]]),
        ...        "labels": torch.tensor([5]),
        ...    }
        ... ]
        >>> metric = GeneralizedIntersectionOverUnion()
        >>> metric(preds, target)
        {'giou': tensor(0.8613)}

    Raises:
        ModuleNotFoundError:
            If torchvision is not installed with version 0.8.0 or newer.

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = True

    _iou_type: str = "giou"
    _invalid_val: float = -1.0

    def __init__(
        self,
        box_format: str = "xyxy",
        iou_threshold: Optional[float] = None,
        class_metrics: bool = False,
        respect_labels: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(box_format, iou_threshold, class_metrics, respect_labels, **kwargs)

    @staticmethod
    def _iou_update_fn(*args: Any, **kwargs: Any) -> Tensor:
        return _giou_update(*args, **kwargs)

    @staticmethod
    def _iou_compute_fn(*args: Any, **kwargs: Any) -> Tensor:
        return _giou_compute(*args, **kwargs)

    def plot(
        self, val: Optional[Union[Tensor, Sequence[Tensor]]] = None, ax: Optional[_AX_TYPE] = None
    ) -> _PLOT_OUT_TYPE:
        """Plot a single or multiple values from the metric.

        Args:
            val: Either a single result from calling `metric.forward` or `metric.compute` or a list of these results.
                If no value is provided, will automatically call `metric.compute` and plot that result.
            ax: An matplotlib axis object. If provided will add plot to that axis

        Returns:
            Figure object and Axes object

        Raises:
            ModuleNotFoundError:
                If `matplotlib` is not installed

        .. plot::
            :scale: 75

            >>> # Example plotting single value
            >>> import torch
            >>> from torchmetrics.detection import GeneralizedIntersectionOverUnion
            >>> preds = [
            ...    {
            ...        "boxes": torch.tensor([[296.55, 93.96, 314.97, 152.79], [298.55, 98.96, 314.97, 151.79]]),
            ...        "scores": torch.tensor([0.236, 0.56]),
            ...        "labels": torch.tensor([4, 5]),
            ...    }
            ... ]
            >>> target = [
            ...    {
            ...        "boxes": torch.tensor([[300.00, 100.00, 315.00, 150.00]]),
            ...        "labels": torch.tensor([5]),
            ...    }
            ... ]
            >>> metric = GeneralizedIntersectionOverUnion()
            >>> metric.update(preds, target)
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> # Example plotting multiple values
            >>> import torch
            >>> from torchmetrics.detection import GeneralizedIntersectionOverUnion
            >>> preds = [
            ...    {
            ...        "boxes": torch.tensor([[296.55, 93.96, 314.97, 152.79], [298.55, 98.96, 314.97, 151.79]]),
            ...        "scores": torch.tensor([0.236, 0.56]),
            ...        "labels": torch.tensor([4, 5]),
            ...    }
            ... ]
            >>> target = lambda : [
            ...    {
            ...        "boxes": torch.tensor([[300.00, 100.00, 335.00, 150.00]]) + torch.randint(-10, 10, (1, 4)),
            ...        "labels": torch.tensor([5]),
            ...    }
            ... ]
            >>> metric = GeneralizedIntersectionOverUnion()
            >>> vals = []
            >>> for _ in range(20):
            ...     vals.append(metric(preds, target()))
            >>> fig_, ax_ = metric.plot(vals)

        """
        return self._plot(val, ax)
