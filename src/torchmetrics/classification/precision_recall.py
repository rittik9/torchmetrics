# Copyright The Lightning team.
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
from typing import Any, Optional, Sequence, Type, Union

from torch import Tensor
from typing_extensions import Literal

from torchmetrics.classification.base import _ClassificationTaskWrapper
from torchmetrics.classification.stat_scores import BinaryStatScores, MulticlassStatScores, MultilabelStatScores
from torchmetrics.functional.classification.precision_recall import (
    _precision_recall_reduce,
)
from torchmetrics.metric import Metric
from torchmetrics.utilities.enums import ClassificationTask
from torchmetrics.utilities.imports import _MATPLOTLIB_AVAILABLE
from torchmetrics.utilities.plot import _AX_TYPE, _PLOT_OUT_TYPE

if not _MATPLOTLIB_AVAILABLE:
    __doctest_skip__ = [
        "BinaryPrecision.plot",
        "MulticlassPrecision.plot",
        "MultilabelPrecision.plot",
        "BinaryRecall.plot",
        "MulticlassRecall.plot",
        "MultilabelRecall.plot",
    ]


class BinaryPrecision(BinaryStatScores):
    r"""Compute `Precision`_ for binary tasks.

    .. math:: \text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}

    Where :math:`\text{TP}` and :math:`\text{FP}` represent the number of true positives and false positives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FP} \neq 0`. If this case is
    encountered a score of `zero_division` (0 or 1, default is 0) is returned.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): A int or float tensor of shape ``(N, ...)``. If preds is a floating point
      tensor with values outside [0,1] range we consider the input to be logits and will auto apply sigmoid per
      element. Additionally, we convert to int tensor with thresholding using the value in ``threshold``.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)``.

    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``bp`` (:class:`~torch.Tensor`): If ``multidim_average`` is set to ``global``, the metric returns a scalar
      value. If ``multidim_average`` is set to ``samplewise``, the metric returns ``(N,)`` vector consisting of a
      scalar value per sample.

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        threshold: Threshold for transforming probability to binary {0,1} predictions
        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FP} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import BinaryPrecision
        >>> target = tensor([0, 1, 0, 1, 0, 1])
        >>> preds = tensor([0, 0, 1, 1, 0, 1])
        >>> metric = BinaryPrecision()
        >>> metric(preds, target)
        tensor(0.6667)

    Example (preds is float tensor):
        >>> from torchmetrics.classification import BinaryPrecision
        >>> target = tensor([0, 1, 0, 1, 0, 1])
        >>> preds = tensor([0.11, 0.22, 0.84, 0.73, 0.33, 0.92])
        >>> metric = BinaryPrecision()
        >>> metric(preds, target)
        tensor(0.6667)

    Example (multidim tensors):
        >>> from torchmetrics.classification import BinaryPrecision
        >>> target = tensor([[[0, 1], [1, 0], [0, 1]], [[1, 1], [0, 0], [1, 0]]])
        >>> preds = tensor([[[0.59, 0.91], [0.91, 0.99],  [0.63, 0.04]],
        ...                 [[0.38, 0.04], [0.86, 0.780], [0.45, 0.37]]])
        >>> metric = BinaryPrecision(multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.4000, 0.0000])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "precision",
            tp,
            fp,
            tn,
            fn,
            average="binary",
            multidim_average=self.multidim_average,
            zero_division=self.zero_division,
        )

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

            >>> from torch import rand, randint
            >>> # Example plotting a single value
            >>> from torchmetrics.classification import BinaryPrecision
            >>> metric = BinaryPrecision()
            >>> metric.update(rand(10), randint(2,(10,)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import rand, randint
            >>> # Example plotting multiple values
            >>> from torchmetrics.classification import BinaryPrecision
            >>> metric = BinaryPrecision()
            >>> values = [ ]
            >>> for _ in range(10):
            ...     values.append(metric(rand(10), randint(2,(10,))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class MulticlassPrecision(MulticlassStatScores):
    r"""Compute `Precision`_ for multiclass tasks.

    .. math:: \text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}

    Where :math:`\text{TP}` and :math:`\text{FP}` represent the number of true positives and false positives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FP} \neq 0`. If this case is
    encountered for any class, the metric for that class will be set to `zero_division` (0 or 1, default is 0) and
    the overall metric may therefore be affected in turn.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)`` or float tensor of shape ``(N, C, ..)``.
      If preds is a floating point we apply ``torch.argmax`` along the ``C`` dimension to automatically convert
      probabilities/logits into an int tensor.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)``.


    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``mcp`` (:class:`~torch.Tensor`): The returned shape depends on the ``average`` and ``multidim_average``
      arguments:

        - If ``multidim_average`` is set to ``global``:

          - If ``average='micro'/'macro'/'weighted'``, the output will be a scalar tensor
          - If ``average=None/'none'``, the shape will be ``(C,)``

        - If ``multidim_average`` is set to ``samplewise``:

          - If ``average='micro'/'macro'/'weighted'``, the shape will be ``(N,)``
          - If ``average=None/'none'``, the shape will be ``(N, C)``

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        num_classes: Integer specifying the number of classes
        average:
            Defines the reduction that is applied over labels. Should be one of the following:

            - ``micro``: Sum statistics over all labels
            - ``macro``: Calculate statistics for each label and average them
            - ``weighted``: calculates statistics for each label and computes weighted average using their support
            - ``"none"`` or ``None``: calculates statistic for each label and applies no reduction
        top_k:
            Number of highest probability or logit score predictions considered to find the correct label.
            Only works when ``preds`` contain probabilities/logits.
        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FP} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import MulticlassPrecision
        >>> target = tensor([2, 1, 0, 0])
        >>> preds = tensor([2, 1, 0, 1])
        >>> metric = MulticlassPrecision(num_classes=3)
        >>> metric(preds, target)
        tensor(0.8333)
        >>> mcp = MulticlassPrecision(num_classes=3, average=None)
        >>> mcp(preds, target)
        tensor([1.0000, 0.5000, 1.0000])

    Example (preds is float tensor):
        >>> from torchmetrics.classification import MulticlassPrecision
        >>> target = tensor([2, 1, 0, 0])
        >>> preds = tensor([[0.16, 0.26, 0.58],
        ...                 [0.22, 0.61, 0.17],
        ...                 [0.71, 0.09, 0.20],
        ...                 [0.05, 0.82, 0.13]])
        >>> metric = MulticlassPrecision(num_classes=3)
        >>> metric(preds, target)
        tensor(0.8333)
        >>> mcp = MulticlassPrecision(num_classes=3, average=None)
        >>> mcp(preds, target)
        tensor([1.0000, 0.5000, 1.0000])

    Example (multidim tensors):
        >>> from torchmetrics.classification import MulticlassPrecision
        >>> target = tensor([[[0, 1], [2, 1], [0, 2]], [[1, 1], [2, 0], [1, 2]]])
        >>> preds = tensor([[[0, 2], [2, 0], [0, 1]], [[2, 2], [2, 1], [1, 0]]])
        >>> metric = MulticlassPrecision(num_classes=3, multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.3889, 0.2778])
        >>> mcp = MulticlassPrecision(num_classes=3, multidim_average='samplewise', average=None)
        >>> mcp(preds, target)
        tensor([[0.6667, 0.0000, 0.5000],
                [0.0000, 0.5000, 0.3333]])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0
    plot_legend_name: str = "Class"

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "precision",
            tp,
            fp,
            tn,
            fn,
            average=self.average,
            multidim_average=self.multidim_average,
            top_k=self.top_k,
            zero_division=self.zero_division,
        )

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

            >>> from torch import randint
            >>> # Example plotting a single value per class
            >>> from torchmetrics.classification import MulticlassPrecision
            >>> metric = MulticlassPrecision(num_classes=3, average=None)
            >>> metric.update(randint(3, (20,)), randint(3, (20,)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import randint
            >>> # Example plotting a multiple values per class
            >>> from torchmetrics.classification import MulticlassPrecision
            >>> metric = MulticlassPrecision(num_classes=3, average=None)
            >>> values = []
            >>> for _ in range(20):
            ...     values.append(metric(randint(3, (20,)), randint(3, (20,))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class MultilabelPrecision(MultilabelStatScores):
    r"""Compute `Precision`_ for multilabel tasks.

    .. math:: \text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}

    Where :math:`\text{TP}` and :math:`\text{FP}` represent the number of true positives and false positives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FP} \neq 0`. If this case is
    encountered for any label, the metric for that label will be set to `zero_division` (0 or 1, default is 0) and
    the overall metric may therefore be affected in turn.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): An int tensor or float tensor of shape ``(N, C, ...)``.
      If preds is a floating point tensor with values outside [0,1] range we consider the input to be logits and
      will auto apply sigmoid per element. Additionally, we convert to int tensor with thresholding using the value
      in ``threshold``.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, C, ...)``.

    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``mlp`` (:class:`~torch.Tensor`): The returned shape depends on the ``average`` and ``multidim_average``
      arguments:

        - If ``multidim_average`` is set to ``global``:

          - If ``average='micro'/'macro'/'weighted'``, the output will be a scalar tensor
          - If ``average=None/'none'``, the shape will be ``(C,)``

        - If ``multidim_average`` is set to ``samplewise``:

          - If ``average='micro'/'macro'/'weighted'``, the shape will be ``(N,)``
          - If ``average=None/'none'``, the shape will be ``(N, C)``

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        num_labels: Integer specifying the number of labels
        threshold: Threshold for transforming probability to binary (0,1) predictions
        average:
            Defines the reduction that is applied over labels. Should be one of the following:

            - ``micro``: Sum statistics over all labels
            - ``macro``: Calculate statistics for each label and average them
            - ``weighted``: calculates statistics for each label and computes weighted average using their support
            - ``"none"`` or ``None``: calculates statistic for each label and applies no reduction

        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FP} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import MultilabelPrecision
        >>> target = tensor([[0, 1, 0], [1, 0, 1]])
        >>> preds = tensor([[0, 0, 1], [1, 0, 1]])
        >>> metric = MultilabelPrecision(num_labels=3)
        >>> metric(preds, target)
        tensor(0.5000)
        >>> mlp = MultilabelPrecision(num_labels=3, average=None)
        >>> mlp(preds, target)
        tensor([1.0000, 0.0000, 0.5000])

    Example (preds is float tensor):
        >>> from torchmetrics.classification import MultilabelPrecision
        >>> target = tensor([[0, 1, 0], [1, 0, 1]])
        >>> preds = tensor([[0.11, 0.22, 0.84], [0.73, 0.33, 0.92]])
        >>> metric = MultilabelPrecision(num_labels=3)
        >>> metric(preds, target)
        tensor(0.5000)
        >>> mlp = MultilabelPrecision(num_labels=3, average=None)
        >>> mlp(preds, target)
        tensor([1.0000, 0.0000, 0.5000])

    Example (multidim tensors):
        >>> from torchmetrics.classification import MultilabelPrecision
        >>> target = tensor([[[0, 1], [1, 0], [0, 1]], [[1, 1], [0, 0], [1, 0]]])
        >>> preds = tensor([[[0.59, 0.91], [0.91, 0.99],  [0.63, 0.04]],
        ...                 [[0.38, 0.04], [0.86, 0.780], [0.45, 0.37]]])
        >>> metric = MultilabelPrecision(num_labels=3, multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.3333, 0.0000])
        >>> mlp = MultilabelPrecision(num_labels=3, multidim_average='samplewise', average=None)
        >>> mlp(preds, target)
        tensor([[0.5000, 0.5000, 0.0000],
                [0.0000, 0.0000, 0.0000]])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0
    plot_legend_name: str = "Label"

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "precision",
            tp,
            fp,
            tn,
            fn,
            average=self.average,
            multidim_average=self.multidim_average,
            multilabel=True,
            zero_division=self.zero_division,
        )

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

            >>> from torch import rand, randint
            >>> # Example plotting a single value
            >>> from torchmetrics.classification import MultilabelPrecision
            >>> metric = MultilabelPrecision(num_labels=3)
            >>> metric.update(randint(2, (20, 3)), randint(2, (20, 3)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import rand, randint
            >>> # Example plotting multiple values
            >>> from torchmetrics.classification import MultilabelPrecision
            >>> metric = MultilabelPrecision(num_labels=3)
            >>> values = [ ]
            >>> for _ in range(10):
            ...     values.append(metric(randint(2, (20, 3)), randint(2, (20, 3))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class BinaryRecall(BinaryStatScores):
    r"""Compute `Recall`_ for binary tasks.

    .. math:: \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}

    Where :math:`\text{TP}` and :math:`\text{FN}` represent the number of true positives and false negatives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FN} \neq 0`. If this case is
    encountered a score of `zero_division` (0 or 1, default is 0) is returned.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): An int tensor or float tensor of shape ``(N, ...)``. If preds is a
      floating point tensor with values outside [0,1] range we consider the input to be logits and will auto apply
      sigmoid per element. Additionally, we convert to int tensor with thresholding using the value in ``threshold``.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)``

    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``br`` (:class:`~torch.Tensor`): If ``multidim_average`` is set to ``global``, the metric returns a scalar
      value. If ``multidim_average`` is set to ``samplewise``, the metric returns ``(N,)`` vector consisting of
      a scalar value per sample.

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        threshold: Threshold for transforming probability to binary {0,1} predictions
        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FN} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import BinaryRecall
        >>> target = tensor([0, 1, 0, 1, 0, 1])
        >>> preds = tensor([0, 0, 1, 1, 0, 1])
        >>> metric = BinaryRecall()
        >>> metric(preds, target)
        tensor(0.6667)

    Example (preds is float tensor):
        >>> from torchmetrics.classification import BinaryRecall
        >>> target = tensor([0, 1, 0, 1, 0, 1])
        >>> preds = tensor([0.11, 0.22, 0.84, 0.73, 0.33, 0.92])
        >>> metric = BinaryRecall()
        >>> metric(preds, target)
        tensor(0.6667)

    Example (multidim tensors):
        >>> from torchmetrics.classification import BinaryRecall
        >>> target = tensor([[[0, 1], [1, 0], [0, 1]], [[1, 1], [0, 0], [1, 0]]])
        >>> preds = tensor([[[0.59, 0.91], [0.91, 0.99],  [0.63, 0.04]],
        ...                 [[0.38, 0.04], [0.86, 0.780], [0.45, 0.37]]])
        >>> metric = BinaryRecall(multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.6667, 0.0000])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "recall",
            tp,
            fp,
            tn,
            fn,
            average="binary",
            multidim_average=self.multidim_average,
            zero_division=self.zero_division,
        )

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

            >>> from torch import rand, randint
            >>> # Example plotting a single value
            >>> from torchmetrics.classification import BinaryRecall
            >>> metric = BinaryRecall()
            >>> metric.update(rand(10), randint(2,(10,)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import rand, randint
            >>> # Example plotting multiple values
            >>> from torchmetrics.classification import BinaryRecall
            >>> metric = BinaryRecall()
            >>> values = [ ]
            >>> for _ in range(10):
            ...     values.append(metric(rand(10), randint(2,(10,))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class MulticlassRecall(MulticlassStatScores):
    r"""Compute `Recall`_ for multiclass tasks.

    .. math:: \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}

    Where :math:`\text{TP}` and :math:`\text{FN}` represent the number of true positives and false negatives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FN} \neq 0`. If this case is
    encountered for any class, the metric for that class will be set to `zero_division` (0 or 1, default is 0) and
    the overall metric may therefore be affected in turn.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)`` or float tensor of shape ``(N, C, ..)``
      If preds is a floating point we apply ``torch.argmax`` along the ``C`` dimension to automatically convert
      probabilities/logits into an int tensor.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, ...)``

    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``mcr`` (:class:`~torch.Tensor`): The returned shape depends on the ``average`` and ``multidim_average``
      arguments:

        - If ``multidim_average`` is set to ``global``:

          - If ``average='micro'/'macro'/'weighted'``, the output will be a scalar tensor
          - If ``average=None/'none'``, the shape will be ``(C,)``

        - If ``multidim_average`` is set to ``samplewise``:

          - If ``average='micro'/'macro'/'weighted'``, the shape will be ``(N,)``
          - If ``average=None/'none'``, the shape will be ``(N, C)``

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        num_classes: Integer specifying the number of classes
        average:
            Defines the reduction that is applied over labels. Should be one of the following:

            - ``micro``: Sum statistics over all labels
            - ``macro``: Calculate statistics for each label and average them
            - ``weighted``: calculates statistics for each label and computes weighted average using their support
            - ``"none"`` or ``None``: calculates statistic for each label and applies no reduction
        top_k:
            Number of highest probability or logit score predictions considered to find the correct label.
            Only works when ``preds`` contain probabilities/logits.
        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FN} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import MulticlassRecall
        >>> target = tensor([2, 1, 0, 0])
        >>> preds = tensor([2, 1, 0, 1])
        >>> metric = MulticlassRecall(num_classes=3)
        >>> metric(preds, target)
        tensor(0.8333)
        >>> mcr = MulticlassRecall(num_classes=3, average=None)
        >>> mcr(preds, target)
        tensor([0.5000, 1.0000, 1.0000])

    Example (preds is float tensor):
        >>> from torchmetrics.classification import MulticlassRecall
        >>> target = tensor([2, 1, 0, 0])
        >>> preds = tensor([[0.16, 0.26, 0.58],
        ...                 [0.22, 0.61, 0.17],
        ...                 [0.71, 0.09, 0.20],
        ...                 [0.05, 0.82, 0.13]])
        >>> metric = MulticlassRecall(num_classes=3)
        >>> metric(preds, target)
        tensor(0.8333)
        >>> mcr = MulticlassRecall(num_classes=3, average=None)
        >>> mcr(preds, target)
        tensor([0.5000, 1.0000, 1.0000])

    Example (multidim tensors):
        >>> from torchmetrics.classification import MulticlassRecall
        >>> target = tensor([[[0, 1], [2, 1], [0, 2]], [[1, 1], [2, 0], [1, 2]]])
        >>> preds = tensor([[[0, 2], [2, 0], [0, 1]], [[2, 2], [2, 1], [1, 0]]])
        >>> metric = MulticlassRecall(num_classes=3, multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.5000, 0.2778])
        >>> mcr = MulticlassRecall(num_classes=3, multidim_average='samplewise', average=None)
        >>> mcr(preds, target)
        tensor([[1.0000, 0.0000, 0.5000],
                [0.0000, 0.3333, 0.5000]])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0
    plot_legend_name: str = "Class"

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "recall",
            tp,
            fp,
            tn,
            fn,
            average=self.average,
            multidim_average=self.multidim_average,
            ignore_index=self.ignore_index,
            top_k=self.top_k,
            zero_division=self.zero_division,
        )

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

            >>> from torch import randint
            >>> # Example plotting a single value per class
            >>> from torchmetrics.classification import MulticlassRecall
            >>> metric = MulticlassRecall(num_classes=3, average=None)
            >>> metric.update(randint(3, (20,)), randint(3, (20,)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import randint
            >>> # Example plotting a multiple values per class
            >>> from torchmetrics.classification import MulticlassRecall
            >>> metric = MulticlassRecall(num_classes=3, average=None)
            >>> values = []
            >>> for _ in range(20):
            ...     values.append(metric(randint(3, (20,)), randint(3, (20,))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class MultilabelRecall(MultilabelStatScores):
    r"""Compute `Recall`_ for multilabel tasks.

    .. math:: \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}

    Where :math:`\text{TP}` and :math:`\text{FN}` represent the number of true positives and false negatives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FN} \neq 0`. If this case is
    encountered for any label, the metric for that label will be set to `zero_division` (0 or 1, default is 0) and
    the overall metric may therefore be affected in turn.

    As input to ``forward`` and ``update`` the metric accepts the following input:

    - ``preds`` (:class:`~torch.Tensor`): An int or float tensor of shape ``(N, C, ...)``. If preds is a floating
      point tensor with values outside [0,1] range we consider the input to be logits and will auto apply sigmoid
      per element. Additionally, we convert to int tensor with thresholding using the value in ``threshold``.
    - ``target`` (:class:`~torch.Tensor`): An int tensor of shape ``(N, C, ...)``

    As output to ``forward`` and ``compute`` the metric returns the following output:

    - ``mlr`` (:class:`~torch.Tensor`): The returned shape depends on the ``average`` and ``multidim_average``
      arguments:

        - If ``multidim_average`` is set to ``global``:

          - If ``average='micro'/'macro'/'weighted'``, the output will be a scalar tensor
          - If ``average=None/'none'``, the shape will be ``(C,)``

        - If ``multidim_average`` is set to ``samplewise``:

          - If ``average='micro'/'macro'/'weighted'``, the shape will be ``(N,)``
          - If ``average=None/'none'``, the shape will be ``(N, C)``

    If ``multidim_average`` is set to ``samplewise`` we expect at least one additional dimension ``...`` to be present,
    which the reduction will then be applied over instead of the sample dimension ``N``.

    Args:
        num_labels: Integer specifying the number of labels
        threshold: Threshold for transforming probability to binary (0,1) predictions
        average:
            Defines the reduction that is applied over labels. Should be one of the following:

            - ``micro``: Sum statistics over all labels
            - ``macro``: Calculate statistics for each label and average them
            - ``weighted``: calculates statistics for each label and computes weighted average using their support
            - ``"none"`` or ``None``: calculates statistic for each label and applies no reduction

        multidim_average:
            Defines how additionally dimensions ``...`` should be handled. Should be one of the following:

            - ``global``: Additional dimensions are flatted along the batch dimension
            - ``samplewise``: Statistic will be calculated independently for each sample on the ``N`` axis.
              The statistics in this case are calculated over the additional dimensions.

        ignore_index:
            Specifies a target value that is ignored and does not contribute to the metric calculation
        validate_args: bool indicating if input arguments and tensors should be validated for correctness.
            Set to ``False`` for faster computations.
        zero_division: Should be `0` or `1`. The value returned when :math:`\text{TP} + \text{FN} = 0`.

    Example (preds is int tensor):
        >>> from torch import tensor
        >>> from torchmetrics.classification import MultilabelRecall
        >>> target = tensor([[0, 1, 0], [1, 0, 1]])
        >>> preds = tensor([[0, 0, 1], [1, 0, 1]])
        >>> metric = MultilabelRecall(num_labels=3)
        >>> metric(preds, target)
        tensor(0.6667)
        >>> mlr = MultilabelRecall(num_labels=3, average=None)
        >>> mlr(preds, target)
        tensor([1., 0., 1.])

    Example (preds is float tensor):
        >>> from torchmetrics.classification import MultilabelRecall
        >>> target = tensor([[0, 1, 0], [1, 0, 1]])
        >>> preds = tensor([[0.11, 0.22, 0.84], [0.73, 0.33, 0.92]])
        >>> metric = MultilabelRecall(num_labels=3)
        >>> metric(preds, target)
        tensor(0.6667)
        >>> mlr = MultilabelRecall(num_labels=3, average=None)
        >>> mlr(preds, target)
        tensor([1., 0., 1.])

    Example (multidim tensors):
        >>> from torchmetrics.classification import MultilabelRecall
        >>> target = tensor([[[0, 1], [1, 0], [0, 1]], [[1, 1], [0, 0], [1, 0]]])
        >>> preds = tensor([[[0.59, 0.91], [0.91, 0.99], [0.63, 0.04]],
        ...                 [[0.38, 0.04], [0.86, 0.780], [0.45, 0.37]]])
        >>> metric = MultilabelRecall(num_labels=3, multidim_average='samplewise')
        >>> metric(preds, target)
        tensor([0.6667, 0.0000])
        >>> mlr = MultilabelRecall(num_labels=3, multidim_average='samplewise', average=None)
        >>> mlr(preds, target)
        tensor([[1., 1., 0.],
                [0., 0., 0.]])

    """

    is_differentiable: bool = False
    higher_is_better: Optional[bool] = True
    full_state_update: bool = False
    plot_lower_bound: float = 0.0
    plot_upper_bound: float = 1.0
    plot_legend_name: str = "Label"

    def compute(self) -> Tensor:
        """Compute metric."""
        tp, fp, tn, fn = self._final_state()
        return _precision_recall_reduce(
            "recall",
            tp,
            fp,
            tn,
            fn,
            average=self.average,
            multidim_average=self.multidim_average,
            multilabel=True,
            zero_division=self.zero_division,
        )

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

            >>> from torch import rand, randint
            >>> # Example plotting a single value
            >>> from torchmetrics.classification import MultilabelRecall
            >>> metric = MultilabelRecall(num_labels=3)
            >>> metric.update(randint(2, (20, 3)), randint(2, (20, 3)))
            >>> fig_, ax_ = metric.plot()

        .. plot::
            :scale: 75

            >>> from torch import rand, randint
            >>> # Example plotting multiple values
            >>> from torchmetrics.classification import MultilabelRecall
            >>> metric = MultilabelRecall(num_labels=3)
            >>> values = [ ]
            >>> for _ in range(10):
            ...     values.append(metric(randint(2, (20, 3)), randint(2, (20, 3))))
            >>> fig_, ax_ = metric.plot(values)

        """
        return self._plot(val, ax)


class Precision(_ClassificationTaskWrapper):
    r"""Compute `Precision`_.

    .. math:: \text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}

    Where :math:`\text{TP}` and :math:`\text{FP}` represent the number of true positives and false positives
    respectively. The metric is only proper defined when :math:`\text{TP} + \text{FP} \neq 0`. If this case is
    encountered for any class/label, the metric for that class/label will be set to 0 and the overall metric may
    therefore be affected in turn.

    This function is a simple wrapper to get the task specific versions of this metric, which is done by setting the
    ``task`` argument to either ``'binary'``, ``'multiclass'`` or ``multilabel``. See the documentation of
    :class:`~torchmetrics.classification.BinaryPrecision`, :class:`~torchmetrics.classification.MulticlassPrecision` and
    :class:`~torchmetrics.classification.MultilabelPrecision` for the specific details of each argument influence and
    examples.

    Legacy Example:
        >>> from torch import tensor
        >>> preds  = tensor([2, 0, 2, 1])
        >>> target = tensor([1, 1, 2, 0])
        >>> precision = Precision(task="multiclass", average='macro', num_classes=3)
        >>> precision(preds, target)
        tensor(0.1667)
        >>> precision = Precision(task="multiclass", average='micro', num_classes=3)
        >>> precision(preds, target)
        tensor(0.2500)

    """

    def __new__(  # type: ignore[misc]
        cls: Type["Precision"],
        task: Literal["binary", "multiclass", "multilabel"],
        threshold: float = 0.5,
        num_classes: Optional[int] = None,
        num_labels: Optional[int] = None,
        average: Optional[Literal["micro", "macro", "weighted", "none"]] = "micro",
        multidim_average: Optional[Literal["global", "samplewise"]] = "global",
        top_k: Optional[int] = 1,
        ignore_index: Optional[int] = None,
        validate_args: bool = True,
        **kwargs: Any,
    ) -> Metric:
        """Initialize task metric."""
        assert multidim_average is not None  # noqa: S101  # needed for mypy
        kwargs.update({
            "multidim_average": multidim_average,
            "ignore_index": ignore_index,
            "validate_args": validate_args,
        })
        task = ClassificationTask.from_str(task)
        if task == ClassificationTask.BINARY:
            return BinaryPrecision(threshold, **kwargs)
        if task == ClassificationTask.MULTICLASS:
            if not isinstance(num_classes, int):
                raise ValueError(f"`num_classes` is expected to be `int` but `{type(num_classes)} was passed.`")
            if not isinstance(top_k, int):
                raise ValueError(f"`top_k` is expected to be `int` but `{type(top_k)} was passed.`")
            return MulticlassPrecision(num_classes, top_k, average, **kwargs)
        if task == ClassificationTask.MULTILABEL:
            if not isinstance(num_labels, int):
                raise ValueError(f"`num_labels` is expected to be `int` but `{type(num_labels)} was passed.`")
            return MultilabelPrecision(num_labels, threshold, average, **kwargs)
        raise ValueError(f"Task {task} not supported!")


class Recall(_ClassificationTaskWrapper):
    r"""Compute `Recall`_.

    .. math:: \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}

    Where :math:`\text{TP}` and :math:`\text{FN}` represent the number of true positives and
    false negatives respectively. The metric is only proper defined when :math:`\text{TP} + \text{FN} \neq 0`. If this
    case is encountered for any class/label, the metric for that class/label will be set to 0 and the overall metric may
    therefore be affected in turn.

    This function is a simple wrapper to get the task specific versions of this metric, which is done by setting the
    ``task`` argument to either ``'binary'``, ``'multiclass'`` or ``multilabel``. See the documentation of
    :class:`~torchmetrics.classification.BinaryRecall`,
    :class:`~torchmetrics.classification.MulticlassRecall` and :class:`~torchmetrics.classification.MultilabelRecall`
    for the specific details of each argument influence and examples.

    Legacy Example:
        >>> from torch import tensor
        >>> preds  = tensor([2, 0, 2, 1])
        >>> target = tensor([1, 1, 2, 0])
        >>> recall = Recall(task="multiclass", average='macro', num_classes=3)
        >>> recall(preds, target)
        tensor(0.3333)
        >>> recall = Recall(task="multiclass", average='micro', num_classes=3)
        >>> recall(preds, target)
        tensor(0.2500)

    """

    def __new__(  # type: ignore[misc]
        cls: Type["Recall"],
        task: Literal["binary", "multiclass", "multilabel"],
        threshold: float = 0.5,
        num_classes: Optional[int] = None,
        num_labels: Optional[int] = None,
        average: Optional[Literal["micro", "macro", "weighted", "none"]] = "micro",
        multidim_average: Optional[Literal["global", "samplewise"]] = "global",
        top_k: Optional[int] = 1,
        ignore_index: Optional[int] = None,
        validate_args: bool = True,
        **kwargs: Any,
    ) -> Metric:
        """Initialize task metric."""
        task = ClassificationTask.from_str(task)
        assert multidim_average is not None  # noqa: S101  # needed for mypy
        kwargs.update({
            "multidim_average": multidim_average,
            "ignore_index": ignore_index,
            "validate_args": validate_args,
        })
        if task == ClassificationTask.BINARY:
            return BinaryRecall(threshold, **kwargs)
        if task == ClassificationTask.MULTICLASS:
            if not isinstance(num_classes, int):
                raise ValueError(f"`num_classes` is expected to be `int` but `{type(num_classes)} was passed.`")
            if not isinstance(top_k, int):
                raise ValueError(f"`top_k` is expected to be `int` but `{type(top_k)} was passed.`")
            return MulticlassRecall(num_classes, top_k, average, **kwargs)
        if task == ClassificationTask.MULTILABEL:
            if not isinstance(num_labels, int):
                raise ValueError(f"`num_labels` is expected to be `int` but `{type(num_labels)} was passed.`")
            return MultilabelRecall(num_labels, threshold, average, **kwargs)
        return None  # type: ignore[return-value]
