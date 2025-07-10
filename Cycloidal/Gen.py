import adsk.core, adsk.fusion, traceback, math

def generate_cyloid(R, E, Rr, gear_ratio, center_hole_radius, points_per_tooth):
    ui = None
    
    N = gear_ratio + 1          # Number of rollers
    
    # # SolidWorks parameters
    # gear_ratio = 10
    
    # R = 10.0                    # Rotor radius
    # E = 0.75                    # Eccentricity  
    # Rr = 1.5                    # Roller radius
    # center_hole_radius = 2.5    # Center hole radius
    
    # points_per_tooth = 6  # Smart sampling uses fewer points
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = app.activeProduct
        rootComponent = design.rootComponent
        
        sketches = rootComponent.sketches
        sketch = sketches.add(rootComponent.xYConstructionPlane)
        rotor_diameter_sketch = sketches.add(rootComponent.xYConstructionPlane)
        
        
        # Enable deferred computation for performance
        sketch.isComputeDeferred = True
        rotor_diameter_sketch.isComputeDeferred = True
        
        #long 
        rotor_circle = rotor_diameter_sketch.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), 
            R
        )
        rotor_circle.isConstruction = True
        
        if center_hole_radius > 0:
            center_hole_circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(E, 0, 0), 
                center_hole_radius
                )
        
        pin_center_point = rotor_diameter_sketch.sketchPoints.add(adsk.core.Point3D.create(R, 0, 0))

        constraints = rotor_diameter_sketch.geometricConstraints
        coincident_constraint = constraints.addCoincident(pin_center_point, rotor_circle)

        first_roller_pin = rotor_diameter_sketch.sketchCurves.sketchCircles.addByCenterRadius(pin_center_point, Rr)
        
        circles = rotor_diameter_sketch.sketchCurves.sketchCircles
        points = rotor_diameter_sketch.sketchPoints
        
        for i in range(1, N):
            angle = (2 * math.pi * i) / N
            pin_x = R * math.cos(angle)
            pin_y = R * math.sin(angle)

            pin_point = points.add(adsk.core.Point3D.create(pin_x * 1.1, pin_y * 1.1, 0))

            constraints.addCoincident(pin_point, rotor_circle)

            pin_circle = circles.addByCenterRadius(pin_point, Rr)
        
        # Use smart sampling to generate points
        points = smart_sample_cycloid(R, E, Rr, N, points_per_tooth)
        
        if len(points) < 3:
            ui.messageBox(f'Only {len(points)} points generated. Need at least 3 for a spline.')
            return
        
        # Create point collection for Fusion
        point_collection = adsk.core.ObjectCollection.create()
        for x, y in points:
            #added eccentric offset
            point = adsk.core.Point3D.create(x + E, y, 0)
            point_collection.add(point)
        
        #dimensions for the pins and rotor
        radial_rotor_dimension = rotor_diameter_sketch.sketchDimensions.addDiameterDimension(
            rotor_circle,
            adsk.core.Point3D.create(R + 1, -5, 0)
        )
        
        pin_diameter_dim = rotor_diameter_sketch.sketchDimensions.addDiameterDimension(
            first_roller_pin,
            adsk.core.Point3D.create(R + Rr + 1, 5, 0)
        )
        
        
        
        # Create cycloid spline
        spline = sketch.sketchCurves.sketchFittedSplines.add(point_collection)
        spline.isClosed = True
        spline.isFixed = False
        
        # Re-enable computation
        sketch.isComputeDeferred = False
        rotor_diameter_sketch.isComputeDeferred = False
        
        ui.messageBox(f'Smart Sampled Cycloid created with {len(points)} points.\n'
                     f'Parameters: R={R}, E={E}, Rr={Rr}, N={N}')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def cycloid_point(t, R, E, Rr, N):
    """Calculate cycloid point using SolidWorks formulas"""
    try:
        numerator = math.sin((1-N)*t)
        denominator = (R/(E*N)) - math.cos((1-N)*t)
        
        if abs(denominator) < 1e-12:
            return None, None
        
        arctan_term = math.atan(numerator/denominator)
        
        x = (R*math.cos(t)) - (Rr*math.cos(t+arctan_term)) - (E*math.cos(N*t))
        y = (-R*math.sin(t)) + (Rr*math.sin(t+arctan_term)) + (E*math.sin(N*t))
        
        if math.isfinite(x) and math.isfinite(y):
            return x, y
        return None, None
    except:
        return None, None

def cycloid_derivative(t, R, E, Rr, N):
    """Calculate derivative (velocity) of cycloid curve"""
    try:
        dt = 1e-8
        x1, y1 = cycloid_point(t - dt, R, E, Rr, N)
        x2, y2 = cycloid_point(t + dt, R, E, Rr, N)
        
        if x1 is None or x2 is None:
            return None, None
            
        dx_dt = (x2 - x1) / (2 * dt)
        dy_dt = (y2 - y1) / (2 * dt)
        
        return dx_dt, dy_dt
    except:
        return None, None

def arc_length_integrand(t, R, E, Rr, N):
    """Calculate the integrand for arc length: sqrt(dx²+dy²)"""
    dx_dt, dy_dt = cycloid_derivative(t, R, E, Rr, N)
    if dx_dt is None or dy_dt is None:
        return 0
    return math.sqrt(dx_dt**2 + dy_dt**2)

def simpson_integration(func, a, b, n, R, E, Rr, N):
    """Simpson's rule integration (from professional script)"""
    if n % 2 == 1:
        n += 1
    
    h = (b - a) / n
    result = func(a, R, E, Rr, N) + func(b, R, E, Rr, N)
    
    for i in range(1, n):
        x = a + i * h
        if i % 2 == 0:
            result += 2 * func(x, R, E, Rr, N)
        else:
            result += 4 * func(x, R, E, Rr, N)
    
    return result * h / 3

def get_arc_length(t1, t2, R, E, Rr, N, subdivisions=100):
    """Calculate arc length between two parameter values"""
    return simpson_integration(arc_length_integrand, t1, t2, subdivisions, R, E, Rr, N)

def bisection_method(func, a, b, tolerance=1e-6, max_iterations=50):
    """Bisection method for root finding (from professional script)"""
    for _ in range(max_iterations):
        c = (a + b) / 2
        if abs(func(c)) < tolerance or abs(b - a) < tolerance:
            return c
        
        if func(a) * func(c) < 0:
            b = c
        else:
            a = c
    
    return (a + b) / 2

def find_parameter_at_arc_length(start_t, target_arc_length, end_t, R, E, Rr, N):
    """Find parameter t where arc length from start_t equals target_arc_length"""
    
    def arc_length_error(t):
        current_length = get_arc_length(start_t, t, R, E, Rr, N)
        return current_length - target_arc_length
    
    try:
        return bisection_method(arc_length_error, start_t, end_t)
    except:
        return start_t + (end_t - start_t) * (target_arc_length / get_arc_length(start_t, end_t, R, E, Rr, N))

def smart_sample_cycloid(R, E, Rr, N, points_per_tooth):
    """
    Smart sampling using arc-length parameterization
    Based on the professional script's approach
    """
    
    num_teeth = N - 1
    tooth_angle = 2 * math.pi / num_teeth
    
    all_points = []
    
    for tooth_num in range(num_teeth):
        tooth_start = tooth_num * tooth_angle
        tooth_end = (tooth_num + 1) * tooth_angle
        
        try:
            tooth_arc_length = get_arc_length(tooth_start, tooth_end, R, E, Rr, N)
            
            if tooth_arc_length <= 0:
                for i in range(points_per_tooth):
                    t = tooth_start + i * tooth_angle / points_per_tooth
                    x, y = cycloid_point(t, R, E, Rr, N)
                    if x is not None:
                        all_points.append((x, y))
                continue
            
            tooth_points = [(tooth_start,)] 
            
            for i in range(1, points_per_tooth):
                target_length = i * tooth_arc_length / points_per_tooth
                
                t = find_parameter_at_arc_length(tooth_start, target_length, tooth_end, R, E, Rr, N)
                
                x, y = cycloid_point(t, R, E, Rr, N)
                if x is not None:
                    all_points.append((x, y))
            
            x_end, y_end = cycloid_point(tooth_end, R, E, Rr, N)
            if x_end is not None:
                all_points.append((x_end, y_end))
                
        except Exception as e:
            print(f"Arc-length sampling failed for tooth {tooth_num}, using uniform: {e}")
            for i in range(points_per_tooth + 1):
                t = tooth_start + i * tooth_angle / points_per_tooth
                x, y = cycloid_point(t, R, E, Rr, N)
                if x is not None:
                    all_points.append((x, y))
    
    critical_points = find_critical_points(R, E, Rr, N, num_teeth)
    all_points.extend(critical_points)
    
    all_points = clean_and_sort_points(all_points)
    
    return all_points

def find_critical_points(R, E, Rr, N, num_teeth):
    """Find critical points like cusps where curvature is maximum"""
    critical_points = []
    tooth_angle = 2 * math.pi / num_teeth
    
    for tooth_num in range(num_teeth):
        tooth_start = tooth_num * tooth_angle
        tooth_end = (tooth_num + 1) * tooth_angle
        
        max_radius = 0
        best_point = None
        
        samples = 20
        for i in range(samples):
            t = tooth_start + i * tooth_angle / samples
            x, y = cycloid_point(t, R, E, Rr, N)
            
            if x is not None:
                radius = math.sqrt(x*x + y*y)
                if radius > max_radius:
                    max_radius = radius
                    best_point = (x, y)
        
        if best_point:
            critical_points.append(best_point)
    
    return critical_points

def clean_and_sort_points(points):
    """Sort points by angle and remove duplicates"""
    def point_angle(point):
        x, y = point
        angle = math.atan2(y, x)
        return angle if angle >= 0 else angle + 2 * math.pi
    
    points.sort(key=point_angle)
    
    cleaned_points = []
    min_distance = 0.001
    
    for point in points:
        if not cleaned_points:
            cleaned_points.append(point)
        else:
            last_point = cleaned_points[-1]
            distance = math.sqrt((point[0] - last_point[0])**2 + (point[1] - last_point[1])**2)
            if distance > min_distance:
                cleaned_points.append(point)
    
    return cleaned_points