Osilaskop X Y düzlemı vektörel cizim razberry pi uzerşnden


Razberry pi kullanarak osiloskob uzerinde xy modunu kullanarak vektorel resim cizer 2 kanalli pwm rc filtre ile birlikte dac gibi davranir ana stream ise dma ytarafindan tasinir cpu bu isin icinde degildir


Bu projeye osiloskopun nasil kullanfigili pwmin nasil calistigi ve rc devrenin nasil insa edilip calistigini anlamak icin basladim projenin sonunda temel seviyede bunlari anladigimi  ve tamamladigimi dusunuyorum


##Devre

2 kanalli 2.2k 2 tane direnc
ile 2 tane 4.7nf kapasitor

ve toprak 


The scope and ADC taps connect to the node between the resistor and the
capacitor, never to the GPIO side of the resistor. The same circuit drawn as a
schematic:


Kediyi 4ms/div  125Ks/s de insa ettik o cviarda diz hat devamliydi


RC zaman Sabiti(tau) =  Rc  10.34 US
RC cutoff frequency 15 kHz
bitr nokta icin gereken zman 32 us= 3 tao t=rc S
 32 khz sectigimiz sabitle

 nokta butcesi 50z saniyede tam tur
 32khz ise saniyede kac nokta cizilecegi 

  her turda 640 nokta

  hz basiqa 640 nokta


  voltajlar piconun gp26 ve gp 27 pinleri tarafinda okunuyor  kucuk sapmalardan dolayi milivot kadar farkli okunabilriler


bilgisiyarabaglabdikta sonra flash uzerinden pmwnin aktardigi veriyi adc ile geri okuyarak belirtli bir gorseli cizer



osiloskop xy moundyken tek noktayi 2 voltajin x ve y ninkonumuna gore yerlestirir tek bir cizgi ile  ciziliyor olmasi bu konuda onemli


circuit pythonun ses cikisi x ve y  degerlerinin gonderilmesinde kullanilir dma kullaniriz  ses kanqlalarini kullanma  sbebimiz circuitpyhonun direct dma apisi olmamasi


nokta butcemizin siniri hazira rtarafinda degil 320000 sample da 650 noktada maksimun 50 hz de kaliyor