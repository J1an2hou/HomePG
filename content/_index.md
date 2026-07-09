---
# Leave the homepage title empty to use the site title
title: Nonlinear Optics
date: 2026
type: landing

sections:
  - block: hero
    content:
      title: |
        Zhou Group @ XJTU
      image:
        filename: NLO.jpg
      text: |
        <br>
        
        **Jian Zhou Research Group** on Nonlinear Optics Simulations.
  
  - block: collection
    content:
      title: Latest News
      subtitle:
      text:
      count: 5
      filters:
        author: ''
        category: ''
        exclude_featured: false
        publication_type: ''
        tag: ''
      offset: 0
      order: desc
      page_type: post
    design:
      view: card
      columns: '1'
  
  - block: markdown
    content:
      title:
      subtitle: ''
      text:
    design:
      columns: '1'
      background:
        image: 
          filename: wel.jpg
          filters:
            brightness: 1
          parallax: false
          position: center
          size: contain
          text_color_light: true
      spacing:
        padding: ['15px', '0', '15px', '0']
      css_class: fullscreen

  - block: collection
    content:
      title: Latest Preprints
      text: ""
      count: 5
      filters:
        folders:
          - publication
        publication_type: 'article'
    design:
      view: citation
      columns: '1'

  - block: markdown
    content:
      title:
      subtitle:
      text: |
        {{% cta cta_link="./people/" cta_text="Explore Us →" %}}
    design:
      columns: '1'
---
