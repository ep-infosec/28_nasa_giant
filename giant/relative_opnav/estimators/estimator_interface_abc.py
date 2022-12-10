# Copyright 2021 United States Government as represented by the Administrator of the National Aeronautics and Space
# Administration.  No copyright is claimed in the United States under Title 17, U.S. Code. All Other Rights Reserved.


"""
This module defines the abstract base class (abc) for defining Relative OpNav techniques that will work with the
:class:`.RelativeOpNav` class.

This abc provides a design guide/requirement for building a new RelNav technique that can be easily registered with
the :class:`.RelativeOpNav` class.  In general, when you define a new RelNav technique, you should subclass this abc
(a) to ensure you implement all of the required methods and instance/class attributes, but also to get some of the
concrete implementations that this class provides which are generally applicable.

You should only worry about this abc when you are defining a new technique.  If you are using an existing technique,
like :mod:`.cross_correlation`, :mod:`.ellipse_matching`, :mod:`.limb_matching`, :mod:`.moment_algorithm`, or
:mod:`.unresolved` then you can ignore this class exists and just read the documentation for those techniques.

Use
---

To implement a fully functional RelNav technique, you must implement the following class attributes.

============================================= ==========================================================================
Class Attribute                               Description
============================================= ==========================================================================
:attr:`~.RelNavEstimator.technique`           A string that gives the name to the technique.  This should be an
                                              "identifier", which means it should be only letters/numbers and the
                                              underscore character, and should not start with a number.  This will be
                                              used in registering the class to define the property that points to the
                                              instance of this technique, as well as the ``{technique}_estimate`` method
                                              and ``{technique}_details`` attribute.
:attr:`~.RelNavEstimator.observable_type`     A list of :class:`.RelNavObservablesType` values that specify what types
                                              of observables are generated by the new technique.  This controls how the
                                              results from the new technique are retrieved and stored by the
                                              :class:`.RelativeOpNav` technique.
:attr:`~.RelNavEstimator.generates_templates` A boolean flag specifying whether this technique generates templates and
                                              stores them in the :attr:`~.RelNavEstimator.templates` attribute.
                                              If this is ``True``, then :class:`.RelativeOpNav` may store the templates
                                              for further investigation by copying the
                                              :attr:`~.RelNavEstimator.templates` attribute.
============================================= ==========================================================================

You also should typically implement the following instance attributes:

============================================= ==========================================================================
Instance Attribute                            Description
============================================= ==========================================================================
:attr:`~.RelNavEstimator.image_processing`    The instance of the image processing class to use when working with the
                                              images.
:attr:`~.RelNavEstimator.scene`               The instance of the :class:`.Scene` class that defines the *a priori*
                                              knowledge of the location/orientation of the targets in the camera frame.
                                              When you are using your custom class with the :class:`.RelativeOpNav`
                                              class and a :class:`.Scene` class then you can assume that the scene
                                              is appropriately set up for each image.
:attr:`~.RelNavEstimator.camera`              The instance of the :class:`.Camera` class which contains the camera model
                                              as well as other images.
:attr:`~.RelNavEstimator.computed_bearings`   The attribute in which to store computed (predicted) bearing measurements
                                              as (x, y) in pixels. This is a list the length of the number of targets in
                                              the scene, and when a target is processed, it should put the bearing
                                              measurements into the appropriate index.  For center finding type
                                              measurements, these will be single (x,y) pairs.  For landmark/limb type
                                              measurements, these will be an nx2 array of (x,y) pairs for each landmark
                                              or feature
:attr:`~.RelNavEstimator.observed_bearings`   The attribute in which to store observed bearing measurements
                                              as (x, y) in pixels. This is a list the length of the number of targets in
                                              the scene, and when a target is processed, it should put the bearing
                                              measurements into the appropriate index.  For center finding type
                                              measurements, these will be single (x,y) pairs.  For landmark/limb type
                                              measurements, these will be an nx2 array of (x,y) pairs for each landmark
                                              or feature
:attr:`~.RelNavEstimator.computed_positions`  The attribute in which to store computed (predicted) positions
                                              measurements as (x, y, z) in kilometers in the camera frame. This is a
                                              list the length of the number of targets in the scene, and when a target
                                              is processed, it should put the predicted position into the appropriate
                                              index.
:attr:`~.RelNavEstimator.observed_positions`  The attribute in which to store observed (measured) positions
                                              measurements as (x, y, z) in kilometers in the camera frame. This is a
                                              list the length of the number of targets in the scene, and when a target
                                              is processed, it should put the measured position into the appropriate
                                              index.
:attr:`~.RelNavEstimator.templates`           The attribute in which templates should be stored for each target if
                                              templates are used for the technique.  This is a list the length of the
                                              number of targets in the scene, and when a target is processed, it should
                                              have the template(s) generated for that target stored in the appropriate
                                              element.  For center finding type techniques the templates are 2D numpy
                                              arrays.  For landmark type techniques the templates are usually lists of
                                              2D numpy arrays, where each list element corresponds to the template for
                                              the corresponding landmark.
:attr:`~.RelNavEstimator.details`             This attribute can be used to store extra information about what happened
                                              when the technique was applied.  This should be a list the length of the
                                              number of targets in the scene, and when a target is processed, the
                                              details should be saved to the appropriate element in the list.  Usually
                                              each element takes the form of a dictionary and contains things like the
                                              uncertainty of the measured value (if known), the correlation score (if
                                              correlation was used) or other pieces of information that are necessarily
                                              directly needed, but which may given context to a user or another program.
                                              Because this is freeform, for the most part GIANT will just copy this list
                                              where it belongs and will not actually inspect the contents. To use the
                                              contents you will either need to inspect them yourself or will need to
                                              write custom code for them.
============================================= ==========================================================================

Finally, we must implement the following method

============================================= ==========================================================================
Method                                        Description
============================================= ==========================================================================
:meth:`~.RelNavEstimator.estimate`            This method should use the defined technique to extract observables from
                                              the image, depending on the type of the observables generated.  This is
                                              also where the computed (predicted) observables should be generated and
                                              stored, as well as fleshing out the :attr:`~.RelNavEstimator.details` and
                                              the :attr:`~.RelNavEstimator.templates` lists if applicable.  This method
                                              should be capable of applying the technique to all targets in the scene,
                                              or to a specifically requested target.
============================================= ==========================================================================

If you implement a class that contains all of these things then you will have successfully defined a new RelNav
technique that can be registered with the :class:`.RelativeOpNav` class.  Whether that technique actually works or not
is up to you however.

For more details on defining/registering a new technique, as well as an example, refer to the
:mod:`~.relative_opnav.estimators` documentation.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Union, List, Any, Optional, Callable, Iterator, Tuple

from giant.ray_tracer.scene import Scene, SceneObject
from giant.camera import Camera
from giant.image_processing import ImageProcessing
from giant._typing import NONEARRAY
from giant.image import OpNavImage


class RelNavObservablesType(Enum):
    """
    This enumeration provides options for the basic types of observables generated in Relative OpNav.

    This is used to set the values for the :attr:`.RelNavEstimator.observable_type` attribute to specify what types of
    observables are generated by a technique.  If you are not implementing your own RelNav technique then you don't need
    to worry about this enumeration really.

    When using this enumeration you can combine multiple types using a list (so
    ``[RelNavObservablesType.RELATIVE_POSITION, RelNavObservablesType.LIMB]`` would specify a RelNav technique that
    generates both a relative position measurement for each image-target pair, as well as individual limb observations
    as bearing measurement).
    """

    CENTER_FINDING = 'CENTER-FINDING'
    """
    A technique that locates the bearing to the center-of-figure of the target in the image.
    """

    LIMB = 'LIMB'
    """
    A technique that identifies the bearings to the limbs of a target in an image.
    """

    LANDMARK = 'LANDMARK'
    """
    A technique that identifies te bearings to the surface features (landmarks) on a target in an image.
    """

    RELATIVE_POSITION = 'RELATIVE-POSITION'
    """
    A technique that identifies the relative position between the camera and the center-of-figure of the target in an 
    image.
    """

    CONSTRAINT = 'CONSTRAINT'
    """
    A technique that identifies the bearings to the same feature in multiple images (whether a known feature or an 
    opportunistic one).
    
    Matching features should be labeled with the same key in different images.  
    """

    CUSTOM = 'CUSTOM'
    """
    A technique that doesn't fall into another category and requires a custom handler.
    
    The custom handler should be stored in the :attr:`.RelNavEstimator.relnav_handler` attribute and should at minimum 
    take a :class:`.RelativeOpNav` instance as the first argument.
    """


class RelNavEstimator(metaclass=ABCMeta):
    """
    This is the abstract base class for all RelNav techniques in GIANT that work with the :class:`.RelativeOpNav` user
    interface.

    A RelNav technique in GIANT is something that extracts observables of targets from an image.  Usually these targets
    are planetary or natural bodies, not stars or man-made objects (though it is possible to have a man made object be a
    target).  There are different variations on what exactly is extracted from the image, but most boil down into either
    a bearing measurement (the pixel location of the target in the image), a relative position measurement (the vector
    from the camera to the target in the camera frame), or a constraint measurement (paired bearing measurements of the
    same target in different images).

    This class serves as a prototype for implementing a new RelNav technique in GIANT.  It defines an abstract method,
    :meth:`estimate` which is the primary interface GIANT will use to apply the technique to extract observables from an
    image.  It also defines some class methods that should be overridden by subclass, including :attr:`technique`,
    :attr:`observable_type`, :attr:`relnav_handler`, and :attr:`generates_templates` which determine how the
    :class:`.RelativeOpNav` class interacts with the new technique.  Finally, it defines some instance attributes,
    :attr:`image_processing`, :attr:`scene`, :attr:`camera:`, :attr:`computed_bearings`, :attr:`observed_bearings`,
    :attr:`computed_positions`, :attr:`observed_positions`, :attr:`templates`, and :attr:`details` which should be used
    for retrieving/storing information during the fit.  This class also defines a concrete method, :meth:`reset`, which
    is used by the :class:`.RelativeOpNav` class to prepare the instance of the technique for a new image/target pair.

    For more details on defining/registering a new technique using this class as a template/super class, see the
    :mod:`~.relative_opnav.estimators` documentation.

    .. note:: Because this is an ABC, you cannot create an instance of this class.
    """

    technique: Optional[str] = None
    """
    The name for the technique for registering with :class:`.RelativeOpNav`.  
    
    If None then the name will default to the name of the module where the class is defined.  
    
    This should typically be all lowercase and should not include any spaces or special characters except for ``_`` as 
    it will be used to make attribute/method names.  (That is ``MyEstimator.technique.isidentifier()`` should evaluate 
    ``True``).
    """

    observable_type: Optional[Union[List[Union[RelNavObservablesType, str]], RelNavObservablesType, str]] = None
    """
    The types of observables that are generated by this technique.  
    
    This should be a list of :class:`.RelNavObservablesType` enum values that specify what type(s) of observables this 
    technique generates.  It can also be ``None`` in which case the default type of 
    :attr:`.RelNavObservablesType.CENTER_FINDING` will be assumed, or it can be a single string or 
    :class:`.RelNavObservable` value if only one type is assumed.  
    
    If this is :attr:`.RelNavObservablesType.CUSTOM`, then that can be the only type, and you must also define a class 
    attribute ``relnav_handler`` which is a function where the first and only positional argument is the 
    :class:`.RelativeOpNav` instance that this technique was registered to and there are 2 key word arguments 
    ``image_ind`` and ``include_targets`` which should be used to control which image/target is processed.
    """

    relnav_handler: Optional[Callable] = None
    """
    A custom handler for doing estimation/packaging the results into the :class:`.RelativeOpNav` instance.
    
    Typically this should be ``None``, unless the :attr:`observable_type` is set to 
    :attr:`.RelNavObservablesType.CUSTOM`, in which case this must be a function where the first and only positional 
    argument is the :class:`.RelativeOpNav` instance that this technique was registered to and there are 2 key word 
    arguments ``image_ind`` and ``include_targets`` which should be used to control which image/target is processed.
    
    If :attr:`observable_type` is not :attr:`.RelNavObservablesType.CUSTOM` then this is ignored whether it is ``None`` 
    or not.
    """

    generates_templates: bool = False
    """
    A flag specifying whether this RelNav estimator generates and stores templates in the :attr:`templates` attribute.
    """

    def __init__(self, scene: Scene, camera: Camera, image_processing: ImageProcessing, **kwargs):
        """
        :param scene: The :class:`.Scene` object containing the target, light, and obscuring objects.
        :param camera: The :class:`.Camera` object containing the camera model and images to be utilized
        :param image_processing: The :class:`.ImageProcessing` object to be used to process the images
        :param kwargs: Extra arguments that the technique may need for settings/other things.  These aren't actually
                       used by this class, but are included so that the type checker doesn't get mad and so you know
                       you can do it.
        """

        self._scene = None
        self._camera = None

        self.image_processing = image_processing  # type: ImageProcessing
        """
        The :class:`.ImageProcessing` instance to use to apply image processing techniques to the images.
        """

        self.scene = scene
        self.camera = camera

        self.computed_bearings = [None] * len(self.scene.target_objs)  # type: List[NONEARRAY]
        """
        A list of the computed (predicted) bearings in the image where each element corresponds to
        the same element in the :attr:`.Scene.target_objs` list.

        The list elements should be numpy arrays or ``None`` if the the target wasn't considered for some reason.  If
        numpy arrays they should contain the pixel locations as (x, y) or (col, row).  This does not always need to be 
        filled out.
        
        This is were you should store results for ``CENTER-FINDING, LIMB, LANDMARK, CONSTRAINT`` techniques.
        """

        self.observed_bearings = [None] * len(self.scene.target_objs)  # type: List[NONEARRAY]
        """
        A list of the observed bearings in the image where each element corresponds to
        the same element in the :attr:`.Scene.target_objs` list.

        The list elements should be numpy arrays or ``None`` if the the target wasn't considered for some reason.  If
        numpy arrays they should contain the pixel locations as (x, y) or (col, row).  This does not always need to be 
        filled out.
        
        This is were you should store results for ``CENTER-FINDING, LIMB, LANDMARK, CONSTRAINT`` techniques.
        """

        self.computed_positions = [None] * len(self.scene.target_objs)  # type: List[NONEARRAY]
        """
        A list of the computed relative position between the target and the camera in the image frame
        where each element corresponds to the same element in the :attr:`.Scene.target_objs` list.

        The list elements should be numpy arrays or ``None`` if the the target wasn't considered or this type of
        measurement is not applicable.  If numpy arrays they should contain the relative position between the camera
        and the target as a length 3 array with units of kilometers in the camera frame. This does not need to be
        populated for all RelNav techniques
        
        This is were you should store results for ``RELATIVE-POSITION`` techniques.
        """


        self.observed_positions = [None] * len(self.scene.target_objs)  # type: List[NONEARRAY]
        """
        A list of the observed relative position between the target and the camera in the image frame
        where each element corresponds to the same element in the :attr:`.Scene.target_objs` list.

        The list elements should be numpy arrays or ``None`` if the the target wasn't considered or this type of
        measurement is not applicable.  If numpy arrays they should contain the relative position between the camera
        and the target as a length 3 array with units of kilometers in the camera frame. This does not need to be
        populated for all RelNav techniques
        
        This is were you should store results for ``RELATIVE-POSITION`` techniques.
        """

        self.templates = [None] * len(self.scene.target_objs)  # type: List[NONEARRAY]
        """
        A list of rendered templates generated by this technique.

        The list elements should be numpy arrays or ``None`` if the the target wasn't considered or this type of
        measurement is not applicable.  If numpy arrays they should contain the templates rendered for the target as 2D 
        arrays.

        If :attr:`generates_templates` is ``False`` this can be ignored.
        """

        self.details = [None] * len(self.scene.target_objs)  # type: List[Optional[Any]]
        """
        This attribute should provide details from applying the technique to each target in the scene.

        The list should be the same length at the :attr:`.Scene.target_objs`.  Typically, if the technique was not 
        applied for some of the targets then the details for the corresponding element should be ``None``.  Beyond each
        element of the details should typically contain a dictionary providing information about the results that is not
        strictly needed for understanding what happened, however, this is not required and you can use whatever 
        structure you want to convey the information.  Whatever you do, however, you should clearly document it for each
        technique so that the user can know what to expect.
        """

        if kwargs:
            print("Can't handle additional kwargs here.  Don't pass them to me!!")

    @property
    def scene(self) -> Scene:
        """
        The scene which defines the a priori locations of all targets and light sources with respect to the camera.

        You can assume that the scene has been updated for the appropriate image time inside of the class.
        """

        return self._scene

    @scene.setter
    def scene(self, val: Scene):

        if isinstance(val, Scene):

            self._scene = val

        else:

            raise ValueError("scene must be a Scene")

    @property
    def camera(self) -> Camera:
        """
        The camera instance that represents the camera used to take the images we are performing Relative OpNav on.

        This is the source of the camera model, and may be used for other information about the camera as well.
        See the :class:`.Camera` property for details.
        """

        return self._camera

    @camera.setter
    def camera(self, val: Camera):

        if isinstance(val, Camera):

            self._camera = val

        else:
            raise ValueError("The camera must be a Camera")

    def target_generator(self, include_targets: Optional[List[bool]]) -> Iterator[Tuple[int, SceneObject]]:
        """
        This method returns a generator which yields target_index, target pairs that are to be processed based on the
        input ``include_targets``.

        If ``include_targets`` is ``None`` then all targets are yielded in the scene.  If it is a list of boolean values
        then only targets where the corresponding index in the list is ``True`` are yielded.

        :param include_targets: The targets to include in the estimation process
        """

        for ind, target in enumerate(self.scene.target_objs):
            if (include_targets is None) or include_targets[ind]:
                yield ind, target

    @abstractmethod
    def estimate(self, image: OpNavImage, include_targets: Optional[List[bool]] = None):
        """
        This method should apply the technique to a specified image for all targets specified in ``include_targets``.

        The results from this method should typically be stored in :attr:`computed_bearings`, :attr:`observed_bearings`,
        :attr:`computed_positions`, :attr:`observed_positions`, :attr:`templates`, and :attr:`details`, depending on the
        type of observables generated.

        When this method is called, you can assume that the scene is set correctly for the input image.

        :param image: The image the technique should be applied to as an OpNavImage
        :param include_targets: An argument specifying which targets should be processed for this image.  If ``None``
                                then all are processed (no, the irony is not lost on me...)
        """
        pass

    def reset(self):
        """
        This method resets the observed/computed attributes as well as the details attribute to have ``None`` for each
        target in :attr:`scene`.

        This method is called by :class:`.RelativeOpNav` between images to ensure that data is not accidentally applied
        from one image to the next.  You can override this method with a subclass to do even more, however, be sure to
        call super().reset() from your override.
        """

        self.computed_bearings = [None] * len(self.scene.target_objs)
        self.observed_bearings = [None] * len(self.scene.target_objs)
        self.computed_positions = [None] * len(self.scene.target_objs)
        self.observed_positions = [None] * len(self.scene.target_objs)
        self.templates = [None] * len(self.scene.target_objs)
        self.details = [None] * len(self.scene.target_objs)