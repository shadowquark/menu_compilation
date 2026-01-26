- [序](introduction.md)
- [第一编　大菜系](chapter1.md)
    <% key="sichuan" %>
    - [第一章　川菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
    <% key="shandong" %>
    - [第二章　鲁菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
    <% key="huaiyang" %>
    - [第三章　淮扬菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
    <% key="guangdong" %>
    - [第四章　粤菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
- [第二编　小菜系](chapter2.md)
    <% key="anhui" %>
    - [第一章　徽菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
    - [第二章　湘菜](test10.md)
    - [第三章　闽菜](test11.md)
    - [第四章　浙菜](test12.md)
    <% key="qingzhen" %>
    - [第五章　清真菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
- [第三编　地方菜](chapter3.md)
    <% key="shanghai" %>
    - [第一章　上海菜](./shanghai/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
- [第四编　官府菜](chapter4.md)
    <% key="tanjia" %>
    - [第一章　谭家菜](./${key}/intro.md)
    %for class1 in data_dict[key]:
        - [${class1[0]}](./${key}/${class1[0]}/index.md)
        %for menu_name in class1[1]:
            - [${menu_name}](./${key}/${class1[0]}/${menu_name}.md)
        %endfor
    %endfor
- [跋](epilogue.md)