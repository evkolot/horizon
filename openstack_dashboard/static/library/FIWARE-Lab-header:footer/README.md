[Guía FIWARE Header & Footer] (https://github.com/ging/horizon/blob/design-header/openstack_dashboard/static/library/FIWARE-Lab-header:footer/README.jpg)

Todos los portales de FIWARE Lab deben usar una cabecera y un pie de página igual, por ello hemos creado una plantilla para que cubra esta necesidad. Está compuesta por los elementos necesarios del framework Bootstrap3, la librería Font awesome, HTML y los css propios de la cabecera y el pié de página.



La carpeta css contiene los estilos, hay que enlazar los archivos: 
  - boottrap-frame.css, 
  - font-awesome.css,  
  - style.css,

con las siguientes líneas de código dentro de la etiqueta <head>

  <link href="css/bootstrap-frame.css" rel="stylesheet" media="screen">
  <link href="css/style.css" rel="stylesheet" media="screen">
  <link href="css/font-awesome.css" rel="stylesheet" media="screen">



En la carpeta fonts tenemos la tipografía corporativa “Neotech” y la fuente de iconos “Font Awesome”. El css necesario se encuentra en style.css



La carpeta img contiene: 
  - favicon.ico
  - avatar por defecto de organizaciones, usuarios y aplicaciones.
  - logo FIWARE y FIWARE Lab



En la carpeta js el archivo collapse.js (procedente de Bootstrap3). Para enlazar el archivo hay que escribir las siguientes líneas antes de cerrar la etiqueta <body>

  <script src="http://code.jquery.com/jquery.js"></script>
  <script src="js/collapse.js"></script>


Por último el código HTML, se encuentra en index.html 
