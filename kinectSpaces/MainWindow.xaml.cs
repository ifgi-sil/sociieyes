# MIT License
#
# Copyright (c) 2020-2024 Violeta Ana Luz Sosa León
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


// violetasdev 
// version 1.0 - kinectSpaces visualization
// Last mod: Jan 2025


using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

using Json = Newtonsoft.Json;
using System.IO;
using System.Timers;


using System.ComponentModel;
using Microsoft.Kinect;
using System.Xml;
using System.Data;
using Newtonsoft.Json;

namespace kinectSpaces
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    /// 
    public enum DisplayFrameType
    {
        Color,
        Body
    }
    public partial class MainWindow : Window, INotifyPropertyChanged
    {

        //General
        private KinectSensor kinectSensor = null;
        private DrawingGroup drawingGroup;
        private DrawingImage imageSource;
        private MultiSourceFrameReader multiSourceFrameReader = null;
        private const DisplayFrameType DEFAULT_DISPLAYFRAMETYPE = DisplayFrameType.Body;
        private int totalVisits = 0;



        // Visualization - RGB

        private WriteableBitmap bitmap = null;
        private FrameDescription currentFrameDescription;
        private DisplayFrameType currentDisplayFrameType;

        // Visualization - Skeleton
        private const float InferredZPositionClamp = 0.1f;

        private CoordinateMapper coordinateMapper = null;
        private Body[] skeletons = null;
        private List<Tuple<JointType, JointType>> bones;
        private List<Pen> skeletonsColors;

        private const double JointThickness = 3;
        private const double ClipBoundsThickness = 10;
        private readonly Brush trackedJointBrush = new SolidColorBrush(Color.FromArgb(255, 68, 192, 68));
        private readonly Brush inferredJointBrush = Brushes.Yellow;
        private readonly Pen inferredBonePen = new Pen(Brushes.Gray, 1);

        private const double HandSize = 20;
        private readonly Brush handClosedBrush = new SolidColorBrush(Color.FromArgb(128, 255, 0, 0));
        private readonly Brush handOpenBrush = new SolidColorBrush(Color.FromArgb(128, 0, 255, 0));
        private readonly Brush handLassoBrush = new SolidColorBrush(Color.FromArgb(128, 0, 0, 255));

        private int displayWidthBody;
        private int displayHeightBody;

        //  Visualization - Movement
        private Body[] bodies = null;

        List<Brush> ellipseBrushes = new List<Brush>();
        public double positionZ = 0;
        public double positionX = 0;


        private Timer saveTimer;
        private List<object> periodicDataStorage = new List<object>();

        private const int MAX_BODIES = 6;
        private List<ulong> bodiesIds = new List<ulong>(MAX_BODIES);

        // Initialize the list with zeroes (similar to the array approach)
        private void InitializeBodiesIds()
        {
            bodiesIds.Clear();
            for (int i = 0; i < MAX_BODIES; i++)
            {
                bodiesIds.Add(0);
            }
        }


        public MainWindow()
        {
            // Initialize the sensor
            this.kinectSensor = KinectSensor.GetDefault();
            this.kinectSensor.IsAvailableChanged += KinectSensor_IsAvailableChanged;
            this.multiSourceFrameReader = this.kinectSensor.OpenMultiSourceFrameReader(FrameSourceTypes.Body | FrameSourceTypes.Color);
            this.multiSourceFrameReader.MultiSourceFrameArrived += this.Reader_MultiSourceFrameArrived;

            SetupCurrentDisplay(DEFAULT_DISPLAYFRAMETYPE);

            // Trajectories
            this.drawingGroup = new DrawingGroup();
            this.imageSource = new DrawingImage(this.drawingGroup);
            this.ellipseIndexColors();
            this.DataContext = this;

            this.kinectSensor.Open();

            InitializeComponent();

            saveTimer = new Timer(1680000); // Set the interval to 1800000 milliseconds (30 minutes)
            saveTimer.Elapsed += OnTimedEvent;
            saveTimer.AutoReset = true;
            saveTimer.Enabled = true;

        }

        public event PropertyChangedEventHandler PropertyChanged;

        private void OnTimedEvent(Object source, ElapsedEventArgs e)
        {
            Application.Current.Dispatcher.Invoke(() => {
                SaveSkeletonData();  // Save the accumulated data
            });
        }

        private void KinectSensor_IsAvailableChanged(object sender, IsAvailableChangedEventArgs e)
        {
            if (e.IsAvailable)
            {
                // Sensor is available, display the camera ID
                DisplayCameraId();
            }

        }

        private void RestartKinectSensor()
        {
            if (this.kinectSensor != null)
            {
                this.kinectSensor.Close();
                this.kinectSensor = KinectSensor.GetDefault();
                this.kinectSensor.Open();
            }
        }

        private void DisplayCameraId()
        {
            if (this.kinectSensor != null && this.kinectSensor.IsOpen)
            {
                string cameraId = this.kinectSensor.UniqueKinectId;
                details_cameraid.Content = $"Camera ID: {cameraId}";
            }
        }

        private void SetupCurrentDisplay(DisplayFrameType newDisplayFrameType)
        {
            currentDisplayFrameType = newDisplayFrameType;
            switch (currentDisplayFrameType)

            {
                case DisplayFrameType.Color:
                    FrameDescription colorFrameDescription = this.kinectSensor.ColorFrameSource.FrameDescription;
                    this.CurrentFrameDescription = colorFrameDescription;
                    // create the bitmap to display
                    this.bitmap = new WriteableBitmap(colorFrameDescription.Width, colorFrameDescription.Height, 96.0, 96.0, PixelFormats.Bgra32, null);
                    break;

                case DisplayFrameType.Body:
                    this.coordinateMapper = this.kinectSensor.CoordinateMapper;
                    FrameDescription bodyDepthFrameDescription = this.kinectSensor.DepthFrameSource.FrameDescription;
                    this.CurrentFrameDescription = bodyDepthFrameDescription;

                    // get size of the scene
                    this.displayWidthBody = bodyDepthFrameDescription.Width;
                    this.displayHeightBody = bodyDepthFrameDescription.Height;

                    // Define a bone as the line between two joints
                    this.bones = new List<Tuple<JointType, JointType>>();
                    // Create the body bones
                    this.defineBoneParts();

                    // Populate body colors that you wish to show, one for each BodyIndex:
                    this.skeletonsColors = new List<Pen>();
                    this.skeletonsIndexColors();

                    // We need to create a drawing group
                    this.drawingGroup = new DrawingGroup();
                    break;

                default:
                    break;
            }
        }

        private void setExperimentData()
        {



            details_start.Content = $"Start Time: {DateTime.Now.ToString("yyy-MM-dd HH:mm:ss")}";

            details_totaldetected.Content = "Total people detected: 0";
        }

        public FrameDescription CurrentFrameDescription
        {
            get { return this.currentFrameDescription; }
            set
            {
                if (this.currentFrameDescription != value)
                {
                    this.currentFrameDescription = value;
                    if (this.PropertyChanged != null)
                    {
                        this.PropertyChanged(this, new PropertyChangedEventArgs("CurrentFrameDescription"));
                    }
                }
            }
        }

        private Path CreateBody(double centerX, double centerY, Brush fillBrush, double size = 15)
        {
            // Create the star shape
            Path star = new Path
            {
                Fill = fillBrush,
                Stroke = Brushes.Black,
                StrokeThickness = 1,
                Data = GenerateStarGeometry(centerX, centerY, size, size / 2) // Star geometry
            };

            // Add the star to the canvas
            fieldOfView.Children.Add(star);

            return star;
        }

        private Geometry GenerateStarGeometry(double centerX, double centerY, double outerRadius, double innerRadius, int numPoints = 5)
        {
            StreamGeometry geometry = new StreamGeometry();

            using (StreamGeometryContext ctx = geometry.Open())
            {
                double angleStep = Math.PI / numPoints; // Half the angle between points
                Point startPoint = new Point(
                    centerX + outerRadius * Math.Cos(0),
                    centerY - outerRadius * Math.Sin(0)
                );

                ctx.BeginFigure(startPoint, true, true);

                for (int i = 1; i <= numPoints * 2; i++)
                {
                    double angle = i * angleStep;
                    double radius = (i % 2 == 0) ? outerRadius : innerRadius;

                    Point point = new Point(
                        centerX + radius * Math.Cos(angle),
                        centerY - radius * Math.Sin(angle)
                    );

                    ctx.LineTo(point, true, false);
                }
            }

            geometry.Freeze();
            return geometry;
        }


        public ImageSource ImageSource
        {
            get
            {
                return this.imageSource;
            }
        }

        private void Reader_MultiSourceFrameArrived(object sender, MultiSourceFrameArrivedEventArgs e)
        {
            // Acquire the multi-source frame
            using (MultiSourceFrame multiSourceFrame = e.FrameReference.AcquireFrame())
            {
                if (multiSourceFrame == null)
                    return;

                // Process body frame
                using (BodyFrame bodyFrame = multiSourceFrame.BodyFrameReference.AcquireFrame())
                {
                    if (bodyFrame != null)
                    {
                        ProcessBodyFrame(bodyFrame);
                    }
                }

                // Handle other frame types based on the current display type
                switch (currentDisplayFrameType)
                {
                    case DisplayFrameType.Body:
                        using (BodyFrame skeletonFrame = multiSourceFrame.BodyFrameReference.AcquireFrame())
                        {
                            if (skeletonFrame != null)
                            {
                                ShowBodyFrame(skeletonFrame);
                            }
                        }
                        break;

                    case DisplayFrameType.Color:
                        using (ColorFrame colorFrame = multiSourceFrame.ColorFrameReference.AcquireFrame())
                        {
                            if (colorFrame != null)
                            {
                                ShowColorFrame(colorFrame);
                            }
                        }
                        break;

                    default:
                        break;
                }
            }
        }

        private void ProcessBodyFrame(BodyFrame bodyFrame)
        {
            // Get the number of bodies in the scene
            bodies = new Body[bodyFrame.BodyFrameSource.BodyCount];
            bodyFrame.GetAndRefreshBodyData(bodies);

            // Save skeleton data to file
            StoreSkeletonData(bodies);

            // Filter tracked bodies
            List<Body> trackedBodies = bodies.Where(body => body.IsTracked).ToList();

            if (trackedBodies.Count == 0)
            {
                ClearTriangle();
                ClearTable();
            }
            else
            {
                // Draw tracked bodies in the scene
                DrawTracked_Bodies(trackedBodies);
            }
        }


        private void ShowBodyFrame(BodyFrame bodyFrame)
        {
            bool dataReceived = false;
            if (bodyFrame != null)
            {

                if (this.skeletons == null)
                {
                    this.skeletons = new Body[bodyFrame.BodyCount];
                }

                // The first time GetAndRefreshBodyData is called, Kinect will allocate each Body in the array.
                // As long as those body objects are not disposed/eliminated and not set to null in the array,
                // those body objects will be re-used.
                bodyFrame.GetAndRefreshBodyData(this.skeletons);
                dataReceived = true;
            }


            if (dataReceived)
            {
                using (DrawingContext dc = this.drawingGroup.Open())
                {
                    // Draw a transparent background to set the render size
                    dc.DrawRectangle(Brushes.Black, null, new Rect(0.0, 0.0, this.displayWidthBody, this.displayHeightBody));

                    int penIndex = 0;
                    foreach (Body body in this.skeletons)
                    {
                        Pen drawPen = this.skeletonsColors[penIndex];

                        if (body.IsTracked)
                        {
                            this.DrawClippedEdges(body, dc);

                            IReadOnlyDictionary<JointType, Joint> joints = body.Joints;

                            // convert the joint points to depth (display) space
                            Dictionary<JointType, Point> jointPoints = new Dictionary<JointType, Point>();

                            foreach (JointType jointType in joints.Keys)
                            {
                                // sometimes the depth(Z) of an inferred joint may show as negative
                                // clamp down to 0.1f to prevent coordinatemapper from returning (-Infinity, -Infinity)
                                CameraSpacePoint position = joints[jointType].Position;
                                if (position.Z < 0)
                                {
                                    position.Z = InferredZPositionClamp;
                                }

                                DepthSpacePoint depthSpacePoint = this.coordinateMapper.MapCameraPointToDepthSpace(position);
                                jointPoints[jointType] = new Point(depthSpacePoint.X, depthSpacePoint.Y);
                            }

                            this.DrawBody(joints, jointPoints, dc, drawPen);
                            this.DrawHand(body.HandLeftState, jointPoints[JointType.HandLeft], dc);
                            this.DrawHand(body.HandRightState, jointPoints[JointType.HandRight], dc);
                        }

                        penIndex++;

                    }

                    // Draw only in the area visible for the camera
                    this.drawingGroup.ClipGeometry = new RectangleGeometry(new Rect(0.0, 0.0, this.displayWidthBody, this.displayHeightBody));
                }
                // Send to our UI/Interface the created bodies to display in the Image:
                FrameDisplayImage.Source = new DrawingImage(this.drawingGroup);

            }
        }

        private void ShowColorFrame(ColorFrame colorFrame)
        {
            if (colorFrame != null)
            {
                FrameDescription colorFrameDescription = colorFrame.FrameDescription;

                using (KinectBuffer colorBuffer = colorFrame.LockRawImageBuffer())
                {
                    this.bitmap.Lock();

                    // verify data and write the new color frame data to the display bitmap
                    if ((colorFrameDescription.Width == this.bitmap.PixelWidth) && (colorFrameDescription.Height == this.bitmap.PixelHeight))
                    {
                        colorFrame.CopyConvertedFrameDataToIntPtr(this.bitmap.BackBuffer, (uint)(colorFrameDescription.Width * colorFrameDescription.Height * 4),
                            ColorImageFormat.Bgra);

                        this.bitmap.AddDirtyRect(new Int32Rect(0, 0, this.bitmap.PixelWidth, this.bitmap.PixelHeight));
                    }

                    this.bitmap.Unlock();
                    FrameDisplayImage.Source = this.bitmap;
                }
            }

        }

        private const int MAX_BODIES = 6;

        private void DrawTrackedBodies(List<Body> trackedBodies)
        {
            bool anyBodyTracked = false;

            // Step 1: Reset untracked IDs
            ResetUntrackedBodies(trackedBodies);

            // Step 2: Process each tracked body
            foreach (var body in trackedBodies)
            {
                ulong currentId = body.TrackingId;

                // Calculate body position
                var position = CalculateBodyPosition(body);
                if (position == null)
                    continue;

                // Check if the body was previously tracked
                int existingIndex = FindExistingBodyIndex(currentId);

                if (existingIndex >= 0)
                {
                    anyBodyTracked = true;
                    UpdateTrackedBody(existingIndex, body, position.Value);
                }
                else
                {
                    AssignNewBody(currentId, body, position.Value);
                }
            }

            // Step 3: Clear visuals if no bodies are tracked
            if (!anyBodyTracked)
            {
                ClearTriangle();
                ClearTable();
            }

            // Update total visits counter
            details_totaldetected.Content = $"Total people detected: {totalVisits}";
        }

        private void ResetUntrackedBodies(List<Body> trackedBodies)
        {
            var trackedIds = new HashSet<ulong>(trackedBodies.Select(b => b.TrackingId));

            for (int i = 0; i < bodiesIds.Length; i++)
            {
                if (bodiesIds[i] != 0 && !trackedIds.Contains(bodiesIds[i]))
                {
                    bodiesIds[i] = 0; // Reset untracked body ID
                }
            }
        }

        private (double X, double Z)? CalculateBodyPosition(Body body)
        {
            const double scaleFactor = 1000.0;

            if (!body.Joints.ContainsKey(JointType.SpineMid))
                return null;

            var joint = body.Joints[JointType.SpineMid];
            double positionZ = fieldOfView.ActualHeight / 5000.0;
            double bodyX = joint.Position.X * positionZ * scaleFactor;
            double bodyZ = joint.Position.Z * positionZ * scaleFactor;

            // Flip Z-axis for visualization
            double flippedBodyZ = fieldOfView.ActualHeight - bodyZ;

            return (bodyX, flippedBodyZ);
        }

        private int FindExistingBodyIndex(ulong trackingId)
        {
            for (int i = 0; i < MAX_BODIES; i++)
            {
                if (bodiesIds[i] == trackingId)
                    return i;
            }
            return -1;
        }

        private void UpdateTrackedBody(int index, Body body, (double X, double Z) position)
        {
            createBody(fieldOfView.ActualWidth / 2 + position.X, position.Z, ellipseBrushes[index]);
            updateTable(index, body.TrackingId, body);
        }

        private void AssignNewBody(ulong trackingId, Body body, (double X, double Z) position)
        {
            for (int i = 0; i < MAX_BODIES; i++)
            {
                if (bodiesIds[i] == 0)
                {
                    bodiesIds[i] = trackingId;
                    createBody(fieldOfView.ActualWidth / 2 + position.X, position.Z, ellipseBrushes[i]);
                    updateTable(i, body.TrackingId, body);
                    totalVisits++;
                    return;
                }
            }
        }

        private void ClearTriangle()
        {
            fieldOfView.Children.Clear();
            drawVisionArea();
        }

        private void ClearTable()
        {
            // Store references to table UI elements in a list
            var coordinateProps = new[] { prop_coordinats_01, prop_coordinats_02, prop_coordinats_03, prop_coordinats_04, prop_coordinats_05, prop_coordinats_06 };
            var orientationProps = new[] { prop_orientation_01, prop_orientation_02, prop_orientation_03, prop_orientation_04, prop_orientation_05, prop_orientation_06 };
            var bodyIdProps = new[] { prop_bodyid_01, prop_bodyid_02, prop_bodyid_03, prop_bodyid_04, prop_bodyid_05, prop_bodyid_06 };

            foreach (var label in coordinateProps.Concat(orientationProps).Concat(bodyIdProps))
            {
                label.Content = string.Empty;
            }
        }


        private void updateTable(int exist_id, int new_id, List<Body> tracked_bodies, ulong current_id)
        {

            switch (exist_id)
            {
                case 0:
                    prop_coordinats_01.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_01.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_01.Content = current_id;
                    break;

                case 1:
                    prop_coordinats_02.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_02.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_02.Content = current_id;
                    break;

                case 2:
                    prop_coordinats_03.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_03.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_03.Content = current_id;
                    break;

                case 3:
                    prop_coordinats_04.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_04.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_04.Content = current_id;
                    break;

                case 4:
                    prop_coordinats_05.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_05.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_05.Content = current_id;
                    break;

                case 5:
                    prop_coordinats_06.Content = coordinatesFieldofView(tracked_bodies[new_id]);
                    prop_orientation_06.Content = getBodyOrientation(tracked_bodies[new_id]);
                    prop_bodyid_06.Content = current_id;
                    break;

                default:
                    break;
            }

        }


        public double getBodyOrientation(Body bodyData)
        {

            double x = bodyData.Joints[JointType.ShoulderRight].Position.X - bodyData.Joints[JointType.ShoulderLeft].Position.X;
            double y = bodyData.Joints[JointType.ShoulderRight].Position.Z - bodyData.Joints[JointType.ShoulderLeft].Position.Z;

            double angle = Math.Round(Math.Atan(y / x) * (180 / Math.PI), 2);

            if (bodyData.Joints[JointType.ShoulderRight].Position.X < bodyData.Joints[JointType.ShoulderLeft].Position.X)
            {
                angle = angle - 90.0;
            }
            else
            {
                angle = angle + 90.0;
            }

            return Math.Round(angle);
        }

        private string coordinatesFieldofView(Body current_body)
        {

            //From the Skeleton Joints we use as position the SpineMid coordinates
            // Remember that Z represents the depth and thus from the perspective of a Cartesian plane it represents Y from a top view
            double coord_y = Math.Round(current_body.Joints[JointType.SpineMid].Position.Z, 2);
            // Remember that X represents side to side movement. The center of the camera marks origin (0,0). 
            double coord_x = Math.Round(current_body.Joints[JointType.SpineMid].Position.X, 2);

            return "X: " + coord_x + " Y: " + coord_y;
        }



        // ***************************************************************************//
        // ************************* BODY DATA PROCESSING **************************//

        /// <summary>
        /// Draws a body
        /// </summary>
        private void DrawBody(IReadOnlyDictionary<JointType, Joint> joints, IDictionary<JointType, Point> jointPoints, DrawingContext drawingContext, Pen drawingPen)
        {
            // Draw the bones
            foreach (var bone in this.bones)
            {
                this.DrawBone(joints, jointPoints, bone.Item1, bone.Item2, drawingContext, drawingPen);
            }

            // Draw the joints
            foreach (JointType jointType in joints.Keys)
            {
                Brush drawBrush = null;

                TrackingState trackingState = joints[jointType].TrackingState;

                if (trackingState == TrackingState.Tracked)
                {
                    drawBrush = this.trackedJointBrush;
                }
                else if (trackingState == TrackingState.Inferred)
                {
                    drawBrush = this.inferredJointBrush;
                }

                if (drawBrush != null)
                {
                    drawingContext.DrawEllipse(drawBrush, null, jointPoints[jointType], JointThickness, JointThickness);
                }
            }
        }

        /// Draws one bone of a body (joint to joint)
        private void DrawBone(IReadOnlyDictionary<JointType, Joint> joints, IDictionary<JointType, Point> jointPoints, JointType jointType0, JointType jointType1, DrawingContext drawingContext, Pen drawingPen)
        {
            // A bone results from the union of two joints/vertices
            Joint joint0 = joints[jointType0];
            Joint joint1 = joints[jointType1];

            // If we can't find either of these joints, we cannot draw them! Exit
            if (joint0.TrackingState == TrackingState.NotTracked ||
                joint1.TrackingState == TrackingState.NotTracked)
            {
                return;
            }

            // We assume all drawn bones are inferred unless BOTH joints are tracked
            Pen drawPen = this.inferredBonePen;
            if ((joint0.TrackingState == TrackingState.Tracked) && (joint1.TrackingState == TrackingState.Tracked))
            {
                drawPen = drawingPen;
            }

            drawingContext.DrawLine(drawPen, jointPoints[jointType0], jointPoints[jointType1]);
        }

        /// Draws a hand symbol if the hand is tracked: red circle = closed, green circle = opened; blue circle = lasso ergo pointing
        private void DrawHand(HandState handState, Point handPosition, DrawingContext drawingContext)
        {
            switch (handState)
            {
                case HandState.Closed:
                    drawingContext.DrawEllipse(this.handClosedBrush, null, handPosition, HandSize, HandSize);
                    break;

                case HandState.Open:
                    drawingContext.DrawEllipse(this.handOpenBrush, null, handPosition, HandSize, HandSize);
                    break;

                case HandState.Lasso:
                    drawingContext.DrawEllipse(this.handLassoBrush, null, handPosition, HandSize, HandSize);
                    break;
            }
        }

        /// Draws indicators to show which edges are clipping body data
        private void DrawClippedEdges(Body body, DrawingContext drawingContext)
        {
            FrameEdges clippedEdges = body.ClippedEdges;

            if (clippedEdges.HasFlag(FrameEdges.Bottom))
            {
                drawingContext.DrawRectangle(
                    Brushes.Indigo,
                    null,
                    new Rect(0, this.displayHeightBody - ClipBoundsThickness, this.displayWidthBody, ClipBoundsThickness));
            }

            if (clippedEdges.HasFlag(FrameEdges.Top))
            {
                drawingContext.DrawRectangle(
                    Brushes.Indigo,
                    null,
                    new Rect(0, 0, this.displayWidthBody, ClipBoundsThickness));
            }

            if (clippedEdges.HasFlag(FrameEdges.Left))
            {
                drawingContext.DrawRectangle(
                    Brushes.Indigo,
                    null,
                    new Rect(0, 0, ClipBoundsThickness, this.displayHeightBody));
            }

            if (clippedEdges.HasFlag(FrameEdges.Right))
            {
                drawingContext.DrawRectangle(
                    Brushes.Indigo,
                    null,
                    new Rect(this.displayWidthBody - ClipBoundsThickness, 0, ClipBoundsThickness, this.displayHeightBody));
            }
        }

        /// <summary>
        ///  This colors are for the bodies detected by the camera, for the Kinect V2 a maximum of 6
        /// </summary>
        private void skeletonsIndexColors()
        {
            this.skeletonsColors.Add(new Pen(Brushes.Navy, 4));
            this.skeletonsColors.Add(new Pen(Brushes.Pink, 4));
            this.skeletonsColors.Add(new Pen(Brushes.Violet, 6));
            this.skeletonsColors.Add(new Pen(Brushes.Red, 4));
            this.skeletonsColors.Add(new Pen(Brushes.Coral, 4));
            this.skeletonsColors.Add(new Pen(Brushes.Green, 4));
        }

        private void ellipseIndexColors()
        {
            this.ellipseBrushes.Add(Brushes.Navy);
            this.ellipseBrushes.Add(Brushes.Pink);
            this.ellipseBrushes.Add(Brushes.Violet);
            this.ellipseBrushes.Add(Brushes.Red);
            this.ellipseBrushes.Add(Brushes.Coral);
            this.ellipseBrushes.Add(Brushes.Green);
        }

        /// <summary>
        /// Define which parts are connected between them
        /// </summary>
        private void defineBoneParts()
        {
            // Torso
            this.bones.Add(new Tuple<JointType, JointType>(JointType.Head, JointType.Neck));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.Neck, JointType.SpineShoulder));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.SpineMid));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineMid, JointType.SpineBase));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.ShoulderRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineShoulder, JointType.ShoulderLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineBase, JointType.HipRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.SpineBase, JointType.HipLeft));

            // Right Arm
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ShoulderRight, JointType.ElbowRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ElbowRight, JointType.WristRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristRight, JointType.HandRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HandRight, JointType.HandTipRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristRight, JointType.ThumbRight));

            // Left Arm
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ShoulderLeft, JointType.ElbowLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.ElbowLeft, JointType.WristLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristLeft, JointType.HandLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HandLeft, JointType.HandTipLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.WristLeft, JointType.ThumbLeft));

            // Right Leg
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HipRight, JointType.KneeRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.KneeRight, JointType.AnkleRight));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.AnkleRight, JointType.FootRight));

            // Left Leg
            this.bones.Add(new Tuple<JointType, JointType>(JointType.HipLeft, JointType.KneeLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.KneeLeft, JointType.AnkleLeft));
            this.bones.Add(new Tuple<JointType, JointType>(JointType.AnkleLeft, JointType.FootLeft));

        }

        private void drawVisionArea()
        {
            // Draw Kinect Vision Area based on the size of our canvas
            int canvasHeight = (int)fieldOfView.ActualHeight;
            int canvasWidth = (int)fieldOfView.ActualWidth;

            PointCollection myPointCollection = new PointCollection();

            //The Kinect has a horizontal field of view opened by 70°, ergo we evaluate a triangle containing one of these angles
            // 35° to each side from the origin

            int x = Convert.ToInt16((canvasHeight * Math.Sin(Math.PI / 180) * 35) + canvasWidth / 2);
            int x1 = Convert.ToInt16(canvasWidth / 2 - (canvasHeight * Math.Sin(Math.PI / 180) * 35));

            // 3 Verticed for the field of view
            myPointCollection.Add(new Point(x, canvasWidth / 2));
            myPointCollection.Add(new Point(x1, canvasWidth / 2));
            myPointCollection.Add(new Point(canvasWidth / 2, canvasHeight));

            //Creating the triangle from the 3 vertices

            Polygon myPolygon = new Polygon();
            myPolygon.Points = myPointCollection;
            myPolygon.Fill = Brushes.GhostWhite;
            myPolygon.Width = canvasWidth;
            myPolygon.Height = canvasHeight;
            myPolygon.Stretch = Stretch.Fill;
            myPolygon.Stroke = Brushes.GhostWhite;
            myPolygon.StrokeThickness = 1;
            myPolygon.Opacity = 1;


            //Add the triangle in our canvas
            gridTriangle.Width = canvasWidth;
            gridTriangle.Height = canvasHeight;
            gridTriangle.Children.Add(myPolygon);
        }


        private void StoreSkeletonData(Body[] bodies)
        {
            var timestamp = DateTime.Now;
            var skeletonData = bodies.Where(b => b.IsTracked).Select(body => new
            {
                CameraId = kinectSensor.UniqueKinectId,
                Timestamp = timestamp,
                BodyId = body.TrackingId,
                Joints = body.Joints.ToDictionary(j => j.Key.ToString(), j => new
                {
                    X = j.Value.Position.X,
                    Y = j.Value.Position.Y,
                    Z = j.Value.Position.Z,
                    TrackingState = j.Value.TrackingState.ToString()
                })
            }).ToList();

            periodicDataStorage.AddRange(skeletonData);
        }

        private void SaveSkeletonData()
        {

            if (periodicDataStorage.Any())
            {
                var json = JsonConvert.SerializeObject(periodicDataStorage, Json.Formatting.Indented);
                string filePath = $@"C:\temp\kinect_{kinectSensor.UniqueKinectId}_{DateTime.Now:_yyyyMMdd_HHmmss}.json";

                // Ensure the directory exists
                string directoryPath = System.IO.Path.GetDirectoryName(filePath);
                if (!Directory.Exists(directoryPath))
                {
                    Directory.CreateDirectory(directoryPath);
                }

                // Write the JSON string to the file
                File.WriteAllText(filePath, json);

                periodicDataStorage.Clear();  // Clear the stored data after saving
            }
        }


        private void Window_Closed(object sender, EventArgs e)
        {
            if (saveTimer != null)
            {
                saveTimer.Stop();
                saveTimer.Dispose();
            }

            SaveSkeletonData();  // Save all remaining data

            if (this.multiSourceFrameReader != null)
            {
                this.multiSourceFrameReader.Dispose();
                this.multiSourceFrameReader = null;
            }



            if (this.kinectSensor != null)
            {
                this.kinectSensor.Close();
                this.kinectSensor = null;
            }


        }

        private void RGB_Click(object sender, RoutedEventArgs e)
        {
            SetupCurrentDisplay(DisplayFrameType.Color);
            RGBButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF9B9BA5"));
            SkeletonButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3F3F46"));
        }

        private void Button_Click(object sender, RoutedEventArgs e)
        {
            SetupCurrentDisplay(DisplayFrameType.Body);
            RGBButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3F3F46"));
            SkeletonButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF9B9BA5"));
        }

        private void Window_Loaded_1(object sender, RoutedEventArgs e)
        {

            setExperimentData();

            drawVisionArea();

        }

        private void CloseWindow_Clic(object sender, RoutedEventArgs e)
        {
            Close();

        }
    }
}
