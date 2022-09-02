# =============================== RESULTADOS ================================ #
# True: cambia las unidades de los resultados a MPa
kgcm2_a_MPa = False
# True: imprime los resultados
printResultados = False
# True: grafica los resultados
graficarResultados = True
# True: lleva los resultados a Excel
Excel = False
# True: agregar compresión sísmica última
Seismic = True
# ============================ DATOS DE ENTRADA ============================= #
#       INGRESAR LOS DATOS CON LAS UNIDADES EN LAS QUE ESTÁN COMENTADOS       #

# ACERO (kg/cm2)
fy = 4_200
Es = 2_100_000

# HORMIGÓN (kg/cm2)
fc = 250

# GEOMETRÍA (cm)
b = 40
h = 65
r = 5

# REFUERZOS
# cabeza superior
phi_superior = 28                   # [mm]
nbarras_superior = 4                # número de barras [un]
ncapas_superior = 1                 # número de capas [un]
separacionbarras_superior = 10      # separación de barras [cm]

# cabeza inferior
phi_inferior = 28                   # [mm]
nbarras_inferior = 4                # número de barras [un]
ncapas_inferior = 1                 # número de capas [un]
separacionbarras_inferior = 10      # separación de barras [cm]

# interior
phi_interior = 25                   # [mm]
nbarras_interior = 2                # número de barras [un]
ncapas_interior = 5                 # número de capas [un]
separacionbarras_interior = 10      # separación de barras [cm]

# cantidad de puntos de eje neutro a evaluar
neje_neutro = 7

# ingresar solicitaciones (estos puntos se ingresan directamente en el diagrama)
# caso default = 0
CC_P1 = 0
CC_M1 = 0

CC_P2 = 0
CC_M2 = 0

CC_P3 = 0
CC_M3 = 0

CC_P4 = 0
CC_M4 = 0

CC_P5 = 0
CC_M5 = 0

CC_P6 = 0
CC_M6 = 0

# ========================== NO MODIFICAR MÁS ABAJO ========================= #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# ========================== NO MODIFICAR MÁS ABAJO ========================= #

comp_sismica = 0.35*b*h*fc/1000

from numpy import pi
ecu = 0.003
esy = fy/Es
sumcapas = sum([ncapas_inferior,ncapas_interior,ncapas_superior])
neje_neutro += 1

CC_P = [CC_P1,CC_P2,CC_P3,CC_P4,CC_P5,CC_P6]
CC_P = [i for i in CC_P if i != 0]
CC_M = [CC_M1,CC_M2,CC_M3,CC_M4,CC_M5,CC_M6]
CC_M = [i for i in CC_M if i != 0]
CC = list(zip(CC_M,CC_P))

# --------------------------------------------------------------------------- #


def cumple_diametro(phi):
    diametro_barras = [8,10,12,16,18,22,25,28,32,36] # [mm]
    assert phi in diametro_barras, f'WARNING --> ¡Cambiar el diámetro de phi{phi} para que cumpla!'
# ver si los diámetros cumplen con los diámetros de fabricación
cumple_diametro(phi_superior),cumple_diametro(phi_inferior),cumple_diametro(phi_interior)

def area_secciones(i,phi_sup,phi_inf,phi_int,nb_sup,nb_inf,nb_int):
    if i+1 <= ncapas_superior:
        area = .25*pi*(phi_sup**2)*nb_sup/100
    elif i+1 <= ncapas_superior+ncapas_interior:
        area = .25*pi*(phi_int**2)*nb_int/100
    else:
        area = .25*pi*(phi_inf**2)*nb_inf/100
    return(area)
areaspos, areasneg = {}, {} # [cm2]
for i in range(sumcapas):
    areaspos[i] = area_secciones(i,phi_superior,phi_inferior,phi_interior,nbarras_superior,nbarras_inferior,nbarras_interior)
    areasneg[i] = area_secciones(i,phi_inferior,phi_superior,phi_interior,nbarras_inferior,nbarras_superior,nbarras_interior)
    

# --------------------------------------------------------------------------- #


# punto de balance
Cpunto_de_balance = (h-r)*Es*ecu/(fy+Es*ecu)

# puntos entre balance y tracción pura
cbt = [round(Cpunto_de_balance*i/neje_neutro,3) for i in range(1,neje_neutro)]
# puntos entre balance y compresión pura
cbc = [round(Cpunto_de_balance+i*(h-Cpunto_de_balance)/(neje_neutro-2),3) for i in range(1,neje_neutro-1)]
cbc.append(round(h*1.1,1))

# puntos de compresión pura, momento puro y tracción pura
Ccompresion_pura = h
Cmomento_puro = min(cbt)
Ctraccion_pura = 0


# --------------------------------------------------------------------------- #


def beta1(fc=fc):
    if 175.7675 <= fc <= 281.228:
        B = .85
    elif 281.228 < fc < 562.456:
        B = .85-.05*(fc/0.070307-4000)/1000
    else:
        B = .65
    return(B)
B1 = beta1()

def separaciones(i):
    if i <= ncapas_superior:
        distancia = i*separacionbarras_superior+r
    elif i >= ncapas_interior + ncapas_superior:
        distancia = h-(sumcapas-i-1)*separacionbarras_inferior-r
    else:
        distancia = separacionbarras_interior+sep[i-1]
    return(distancia)
sep = {}
for i in range(sumcapas):
    sep[i] = separaciones(i)

def comportamiento(c, i, bal, info, A):
    a = c*B1
    distancia = sep[i]
    if distancia < c:
        trac_comp = 'Com'
    else:
        trac_comp = 'Trac'
    es = ecu*(-distancia+c)/c
    if es >= esy:
        fs = fy
    elif es >= -esy:
        fs = es*Es
    else:
        fs = -fy
    if distancia < a:
        Fs1 = A*(fs-.85*fc)
    else:
        Fs1 = A*fs
    M = Fs1*(h/2-distancia)
    # SI EL USUARIO QUIERE, PUEDE IMPRIMIR ESTA INFORMACION PARA VER MÁS DETALLES
    info[distancia] = [trac_comp,es,fs,Fs1,M]
    bal['Pn'] += Fs1
    bal['Mn'] += M

def ES(es):
    if es > .05:
        es = '>0.05'
    elif es < .0002:
        es = '<0.0002'
    else:
        es = round(es,4)
    return(es)

def PHI(es):
    if es == '>0.05':
        phi = .9
    elif es == '<0.0002':
        phi = .65
    elif es > .005:
        phi = .9
    elif es < .002:
        phi = .65
    else:
        phi = .65 + (es-.002)*(.9-.65)/(.005-.002)
    return(round(phi,2))

def tipo_de_falla(es):
    if es == '>0.05':
        tipo_falla = 'Falla por tracción'
    elif es == '<0.0002':
        tipo_falla = 'Falla por compresión'
    elif .005 < es:
        tipo_falla = 'Falla por tracción'
    elif .002 <= es <= .005:
        tipo_falla = 'Transición'
    else:
        tipo_falla = 'Falla por compresión'
    return(tipo_falla)


# --------------------------------------------------------------------------- #


# COMPRESIÓN PURA Y TRACCIÓN PURA
comp_pura = {'Pn':((b*h-sum(areaspos.values()))*0.85*fc+sum(areaspos.values())*fy)/1000, 'Mn':0, 'c':Ccompresion_pura}
trac_pura = {'Pn':sum(areaspos.values())*fy/1000, 'Mn':0, 'c':Ctraccion_pura}
# punto de mayor compresión:
Pmax = 0.8*comp_pura['Pn']


resumen, resumenneg = {}, {}
# máxima tracción
bal1, informacion1, es1 = {'Pn':0, 'Mn':0}, {}, 0
for i in range(sumcapas):
    comportamiento(0.00001,i,bal1,informacion1,areaspos[i])
    if es1 > informacion1[sep[i]][1]:
        es1 = informacion1[sep[i]][1]    
maxtrac = {'Pn':(bal1['Pn']+0.85*fc*b*0.00001*B1)/1000,'Mn':(bal1['Mn']+0.85*0.00001*B1*fc*b*(h/2-0.00001*B1/2))/100000,'c':0.00001}
es1 = ES(-es1)
resumen['Tracción máxima'] = {'Pn':maxtrac['Pn'],'Mn':round(maxtrac['Mn'],3),'es':es1}
resumenneg['Tracción máxima'] = {'Pn':maxtrac['Pn'],'Mn':round(maxtrac['Mn'],3),'es':es1}


# comportamiento puntos entre balance y tracción pura
bal_tracPura_pos, bal_tracPura_neg, informacion2, es2, informacion22, es22 = {}, {}, {}, {}, {}, {}
for c in cbt:
    bal2, info2, es_2 = {'Pn':0,'Mn':0}, {}, 0
    for i in range(sumcapas):
        comportamiento(c,i,bal2,info2,areaspos[i])
        if es_2 > info2[sep[i]][1]:
            es_2 = info2[sep[i]][1]
    bal_tracPura_pos[c] = {'Pn':(0.85*b*B1*c*fc+bal2['Pn'])/1000,'Mn':(0.85*b*B1*c*fc*(h/2-B1*c/2)+bal2['Mn'])/100000}
    es2[c] = ES(-es_2)
    informacion2[c] = info2
    bal22, info22, es_22 = {'Pn':0,'Mn':0}, {}, 0
    for i in range(sumcapas):
        comportamiento(c,i,bal22,info22,areasneg[i])
        if es_22 > info22[sep[i]][1]:
            es_22 = info22[sep[i]][1]
    bal_tracPura_neg[c] = {'Pn':(0.85*b*B1*c*fc+bal22['Pn'])/1000,'Mn':-(0.85*b*B1*c*fc*(h/2-B1*c/2)+bal22['Mn'])/100000}
    es22[c] = ES(-es_22)
    informacion22[c] = info22
    resumen[c] = {'Pn':bal_tracPura_pos[c]['Pn'],'Mn':bal_tracPura_pos[c]['Mn'],'es':es2[c]}
    resumenneg[c] = {'Pn':bal_tracPura_neg[c]['Pn'],'Mn':bal_tracPura_neg[c]['Mn'],'es':es22[c]}

# comportamiento en balance
bal3, informacion3, es3, bal33, informacion33, es33 = {'Pn':0, 'Mn':0}, {}, 0, {'Pn':0, 'Mn':0}, {}, 0
for i in range(sumcapas):
    comportamiento(Cpunto_de_balance,i,bal3,informacion3,areaspos[i])
    if es3 > informacion3[sep[i]][1]:
        es3 = informacion3[sep[i]][1]
    comportamiento(Cpunto_de_balance,i,bal33,informacion33,areasneg[i])
    if es33 > informacion33[sep[i]][1]:
        es33 = informacion33[sep[i]][1]
balancepos = {'Pn':(bal3['Pn']+0.85*fc*b*Cpunto_de_balance*B1)/1000,'Mn':(bal3['Mn']+0.85*Cpunto_de_balance*B1*fc*b*(h/2-Cpunto_de_balance*B1/2))/100000,'c':Cpunto_de_balance,'B1':B1}
balanceneg = {'Pn':(bal33['Pn']+0.85*fc*b*Cpunto_de_balance*B1)/1000,'Mn':-(bal33['Mn']+0.85*Cpunto_de_balance*B1*fc*b*(h/2-Cpunto_de_balance*B1/2))/100000,'c':Cpunto_de_balance,'B1':B1}
es3 = ES(-es3)
es33 = ES(-es33)
resumen['Balance'] = {'Pn':balancepos['Pn'],'Mn':balancepos['Mn'],'es':es3}
resumenneg['Balance'] = {'Pn':balanceneg['Pn'],'Mn':balanceneg['Mn'],'es':es33}


# comportamiento puntos entre balance y compresión pura
# para max(cbc) -> entre máxima compresión y máximo largo sección
bal_compPura_pos, bal_compPura_neg, informacion4, es4, informacion44, es44 = {}, {}, {}, {}, {}, {}
for c in cbc:
    bal4, info4, es_4 = {'Pn':0,'Mn':0}, {}, 0
    for i in range(sumcapas):
        comportamiento(c,i,bal4,info4,areaspos[i])
        if es_4 > info4[sep[i]][1]:
            es_4 = info4[sep[i]][1]
    if (0.85*b*B1*c*fc+bal4['Pn'])/1000>Pmax:
        Pn = Pmax
    else:
        Pn = (0.85*b*B1*c*fc+bal4['Pn'])/1000
    bal44, info44, es_44 = {'Pn':0,'Mn':0}, {}, 0
    for i in range(sumcapas):
        comportamiento(c,i,bal44,info44,areasneg[i])
        if es_44 > info44[sep[i]][1]:
            es_44 = info44[sep[i]][1]
    if (0.85*b*B1*c*fc+bal44['Pn'])/1000>Pmax:
        Pn = Pmax
    else:
        Pn = (0.85*b*B1*c*fc+bal44['Pn'])/1000
    bal_compPura_pos[c] = {'Pn':Pn,'Mn':(0.85*b*B1*c*fc*(h/2-B1*c/2)+bal4['Mn'])/100000}
    bal_compPura_neg[c] = {'Pn':Pn,'Mn':-(0.85*b*B1*c*fc*(h/2-B1*c/2)+bal44['Mn'])/100000}
    es4[c] = ES(-es_4)
    es44[c] = ES(-es_44)
    informacion4[c] = info4
    informacion44[c] = info44
    resumen[c] = {'Pn':bal_compPura_pos[c]['Pn'],'Mn':bal_compPura_pos[c]['Mn'],'es':es4[c]}
    resumenneg[c] = {'Pn':bal_compPura_neg[c]['Pn'],'Mn':bal_compPura_neg[c]['Mn'],'es':es44[c]}
resumen['Compresión Pura'] = {'Pn':Pmax,'Mn':comp_pura['Mn'],'es':'<0.0002'}


# --------------------------------------------------------------------------- #


for key in resumen:
    resumen[key]['phi'] = PHI(resumen[key]['es'])
    resumen[key]['falla'] = tipo_de_falla(resumen[key]['es'])
    resumen[key]['phi*Pn'] = resumen[key]['phi']*resumen[key]['Pn']
    resumen[key]['phi*Mn'] = resumen[key]['phi']*resumen[key]['Mn']
for key in resumenneg:
    resumenneg[key]['phi'] = PHI(resumenneg[key]['es'])
    resumenneg[key]['falla'] = tipo_de_falla(resumenneg[key]['es'])
    resumenneg[key]['phi*Pn'] = resumenneg[key]['phi']*resumenneg[key]['Pn']
    resumenneg[key]['phi*Mn'] = resumenneg[key]['phi']*resumenneg[key]['Mn']


# --------------------------------------------------------------------------- #


if kgcm2_a_MPa:
    for k, v in resumen.items():
        v["Pn"] = v["Pn"]*9.96402
        v["Mn"] = v["Mn"]*9.96402
        v["phi*Pn"] = v["phi*Pn"]*9.96402
        v["phi*Mn"] = v["phi*Mn"]*9.96402
    for k, v in resumenneg.items():
        v["Pn"] = v["Pn"]*9.96402
        v["Mn"] = v["Mn"]*9.96402
        v["phi*Pn"] = v["phi*Pn"]*9.96402
        v["phi*Mn"] = v["phi*Mn"]*9.96402
        
        
if printResultados:
    if kgcm2_a_MPa:
        print('\t<<< RESULTADOS ESTÁN EN KN Y KN×M >>>')
    else:
        print('\t<<< RESULTADOS ESTÁN EN TONF Y TONF×M >>>')
    for k, v in resumen.items():
        print(f'c: {k} Pn: {round(v["Pn"],2):_} Mn: {round(v["Mn"],2):_} es: {v["es"]} Fase: {v["falla"]} ɸ: {v["phi"]} ɸPn: {round(v["phi*Pn"],2):_} ɸMn: {round(v["phi*Mn"],2):_}\n')
    for k, v in reversed(resumenneg.items()):
        skip_line = "\n" if k != "Tracción máxima" else ""
        print(f'c: {k} Pn: {round(v["Pn"],2):_} Mn: {round(v["Mn"],2):_} es: {v["es"]} Fase: {v["falla"]} ɸ: {v["phi"]} ɸPn: {round(v["phi*Pn"],2):_} ɸMn: {round(v["phi*Mn"],2):_} {skip_line}')


if graficarResultados:
    import plotly.graph_objects as go
    import plotly.io as pio
    pio.renderers.default = 'browser'
    if kgcm2_a_MPa:
        un_P, un_M = 'Carga Axial, P [kN]','Momento, M [kN-m]'
    else:
        un_P, un_M = 'Carga Axial, P [tonf]','Momento, M [tonf-m]'
    fig = go.Figure()
    P, M, phiP, phiM = [], [], [], []
    for k, v in resumen.items():
        P.append(v["Pn"])
        M.append(v["Mn"])
        phiP.append(v["phi*Pn"])
        phiM.append(v["phi*Mn"])

    for k, v in reversed(resumenneg.items()):
        P.append(v["Pn"])
        M.append(v["Mn"])
        phiP.append(v["phi*Pn"])
        phiM.append(v["phi*Mn"])

    fig.add_trace(go.Scatter(x=M,y=P,mode='lines+markers',name='Pn-Mu',marker=dict(size=7,line_width=1.5)))
    fig.add_trace(go.Scatter(x=phiM,y=phiP,mode='lines+markers',name='ɸPn-ɸMu',marker=dict(size=7,line_width=1.5)))
    fig.add_trace(go.Scatter(x=CC_M,y=CC_P,mode='markers',name='Combinaciones de Carga',marker=dict(size=7,color='#CDCDCD',line_width=1.5)))
    if Seismic:
        fig.add_trace(go.Scatter(x=[resumen["Balance"]["Mn"]*1.005, resumenneg["Balance"]["Mn"]*1.005],y=[comp_sismica,comp_sismica],mode='lines',name="0.35*fc'*Ag",marker=dict(size=7,line_width=1.5)))
    fig.update_layout(title={'text':'DIAGRAMA DE INTERACCIÓN',
                             'y':0.95,
                             'x':0.5,
                             'xanchor': 'center',
                             'yanchor': 'top'},
                      xaxis_title=un_M,
                      yaxis_title=un_P,
                      font=dict(family="Courier New, monospace",size=18,color="#292421"))
    fig.show()
    
    
if Excel:
    import xlsxwriter
    workbook = xlsxwriter.Workbook('RESULTADOS DIAGRAMA DE INTERACCIÓN.xlsx')
    worksheet = workbook.add_worksheet('RESULTADOS')
    titulos = workbook.add_format()
    titulos.set_center_across(),titulos.set_bold(),titulos.set_border(),titulos.set_bg_color('#ADD8E6')
    resto = workbook.add_format()
    resto.set_border(),resto.set_text_wrap(),resto.set_shrink(),resto.set_align('center'),resto.set_align('vcenter')
    worksheet.write(0,0,'RESUMEN',titulos),worksheet.write(0,1,'',titulos),worksheet.write(0,2,'',titulos),worksheet.write(0,3,'',titulos),worksheet.write(0,4,'',titulos),worksheet.write(0,5,'',titulos),worksheet.write(0,6,'',titulos),worksheet.write(0,7,'',titulos)
    worksheet.write(1,0,'c',titulos),worksheet.write(1,1,'Pn',titulos),worksheet.write(1,2,'Mn',titulos),worksheet.write(1,3,'ɛsTrac',titulos),worksheet.write(1,4,' ',titulos),worksheet.write(1,5,'ɸ',titulos),worksheet.write(1,6,'ɸPn',titulos),worksheet.write(1,7,'ɸMn',titulos)
    row = 2
    for k, v in resumen.items():
        if str(type(k)) == "<class 'str'>":
            worksheet.write(row, 0, k,resto)
        else:
            worksheet.write(row, 0, round(k,1),resto)
        worksheet.write(row, 1, round(v['Pn'],1),resto),worksheet.write(row, 2, round(v['Mn'],1),resto),worksheet.write(row, 3, v['es'],resto),worksheet.write(row, 4, v['falla'],resto),worksheet.write(row, 5, v['phi'],resto),worksheet.write(row, 6, round(v['phi*Pn'],1),resto),worksheet.write(row, 7, round(v['phi*Mn'],1),resto)
        row += 1
    for k, v in reversed(resumenneg.items()):
        if str(type(k)) == "<class 'str'>":
            worksheet.write(row, 0, k,resto)
        else:
            worksheet.write(row, 0, round(k,1),resto)
        worksheet.write(row, 1, round(v['Pn'],1),resto),worksheet.write(row, 2, round(v['Mn'],1),resto),worksheet.write(row, 7, round(v['phi*Mn'],1),resto),worksheet.write(row, 3, v['es'],resto),worksheet.write(row, 4, v['falla'],resto),worksheet.write(row, 5, v['phi'],resto),worksheet.write(row, 6, round(v['phi*Pn'],1),resto)
        row += 1
    workbook.close()
# ============================= CODE ENDS HERE ============================== #