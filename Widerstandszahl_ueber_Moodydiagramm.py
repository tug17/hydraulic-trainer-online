import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

def moody_resistance(k, v, d):
    
    visc = 1.31 * 10**(-6)               #water viscosity
    Re = (v * d) / visc                 #Reynold's number
    d_zu_k = d / k 
    
    print()
    
    if Re >= 2320:

        if d_zu_k > 300000:
            fcn = lambda x: (2*np.log10(Re*np.sqrt(x)/2.51)
                             *np.sqrt(x)-1)
            sol = fsolve(fcn, 0.01)
            lam = sol
            case = "t_S_h_g_B"
            
        elif 100 <= d_zu_k <= 300000:
            fcn = lambda x: (-2*np.log10((2.51/(Re*np.sqrt(x)))+(k/(3.71*d)))
                             *np.sqrt(x)-1)
            sol = fsolve(fcn, 0.01)
            lam = sol
            case = "t_S_Ü"
            
        elif d_zu_k < 100:
            fcn = lambda x: (2*np.log10(3.71*d/k)
                             *np.sqrt(x)-1)
            sol = fsolve(fcn, 0.01)
            lam = sol
            case = "t_S_h_r_B"
        
    elif Re == 2320:
          case = "krit. Re-Zahl = 2320"
    else:
          lambda_lam = 64 / Re
          lam = lambda_lam
          case = "l_S"
    
    print(Re)
    print(lam)
    print(case)
    return Re, d_zu_k, lam




def plot_moody_chart(Re, lam):

    image = plt.imread("Moody_Diagramm_Ausschnitt.jpg")     #load chart
    
    fig = plt.figure(0, dpi=300)
    plt.imshow(image)                                       #show chart

    
    Re_adj = 331.75 * np.log10(Re) - 995.25
    lam_adj = -850 * np.log10(lam) - 850

    plt.title("Widerstandszahl für Rohrleitungen")
    plt.xlabel('Reynoldszahl Re')
    plt.ylabel('Rohrreibungszahl')
    
    x1 = [0,120.5]
    y1 = [0,0]
    y2 = [850,850]
    plt.fill_between(x1,y1,y2, alpha=0.2, color='r')
    
    x2 = [120.5,331.55]
    y2 = [0,0]
    y3 = [850,850]
    plt.fill_between(x2,y2,y3, alpha=0.2, color='b')
    
    x3 = [331.55,1327]
    y3 = [0,0]
    y4 = [850,850]
    plt.fill_between(x3,y3,y4, alpha=0.2, color='g')
    
    
    
    plt.scatter(Re_adj, lam_adj, color='r')            #plot point
    
    
    plt.xlim(0,1327)
    plt.ylim(850,0)
    
    ax = plt.gca()
    ax.set_xticks([0,120.5,331.55,662.85,994.8,1327])
    ax.set_xticklabels(['$10^3$','2320','$10^4$','$10^5$','$10^6$','$10^7$'])

    ax2 = plt.gca()
    ax2.set_yticks([0,38,81,130.5,187.95,254.6,
                    336.7,443,592,850])
    ax2.set_yticklabels([0.10,0.09,0.08,0.07,0.06,0.05,
                         0.04,0.03,0.02,0.01])

 
    


         
k = 10**(-3) * 0.05                #[Eingabe in mm]
v = 0.5
d = 1.5
Re, d_zu_k, lam = moody_resistance(k,v,d)
plot_moody_chart(Re, lam)

# fname = "Moody_Diagramm.jpg"
# X = plt.imread(fname)
# plt.imshow(X)


